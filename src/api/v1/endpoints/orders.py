from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from brokers.jupiter_market import JupiterMarket
from core.database import get_session
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.pairs_repository import PairsRepository
from repositories.prices_repository import PricesRepository
from schemas.orders_schemas import (
    BuyTokensResponse,
    OrderAction,
    OrderStatus,
    SellOrderDetails,
    SellTokensResponse,
)
from schemas.tokens_schemas import (
    BuyTokensRequest,
    SellTokensRequest,
)
from services.transaction_service import TransactionService
from services.wallet_service import WalletService

router = APIRouter()


@router.post("/buy", response_model=BuyTokensResponse)
async def buy_tokens(
    request: BuyTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    order_buy_repository = OrderBuyRepository(db_session)
    pairs_repository = PairsRepository(db_session)
    price_repository = PricesRepository(db_session)

    # TODO: Getting broker service from pair settings
    market_service = JupiterMarket()
    wallet_service = WalletService()
    transaction_service = TransactionService(
        wallet_service,
        market_service,
    )

    pair_id = request.pair_id
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    from_token = pair.from_token
    to_token = pair.to_token
    last_price = await price_repository.get_latest(pair.to_token_id)

    transaction_result = await transaction_service.buy(
        from_token=from_token,
        to_token=to_token,
        buy_amount=request.amount,
        last_market_price=last_price,
    )

    if not transaction_result:
        raise HTTPException(
            status_code=400,
            detail="Transaction failed: unable to complete the buy order.",
        )

    result = await order_buy_repository.create(
        from_token_id=pair.from_token_id,
        to_token_id=pair.to_token_id,
        from_token_amount=transaction_result.send_amount,
        to_token_amount=transaction_result.receive_amount,
        price=transaction_result.price,
    )

    return BuyTokensResponse(
        id=result.id,
        created=result.created,
        status=OrderStatus.OK,
        token=result.to_token.name,
        action=OrderAction.BUY,
        amount=result.to_token_amount,
        price=result.price,
    )


@router.post("/sell", response_model=SellTokensResponse)
async def sell_tokens(
    request: SellTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    order_buy_repository = OrderBuyRepository(db_session)
    order_sell_repository = OrderSellRepository(db_session)
    pairs_repository = PairsRepository(db_session)
    price_repository = PricesRepository(db_session)

    # TODO: Getting broker service from pair settings
    market_service = JupiterMarket()
    wallet_service = WalletService()
    transaction_service = TransactionService(
        wallet_service,
        market_service,
    )

    pair_id = request.pair_id
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    order_id = request.order_id
    order = await order_buy_repository.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order id {order_id} not found",
        )

    last_price = await price_repository.get_latest(pair.to_token_id)

    from_token = pair.to_token
    to_token = pair.from_token
    required_token_amount = int(order.to_token_amount)

    transaction_result = await transaction_service.sell(
        from_token=from_token,
        to_token=to_token,
        sell_token_amount=required_token_amount,
        last_market_price=last_price,
    )

    if not transaction_result:
        raise HTTPException(
            status_code=400,
            detail="Transaction failed: unable to complete the sell order.",
        )

    result = await order_sell_repository.create(
        from_token_id=pair.to_token_id,
        to_token_id=pair.from_token_id,
        from_token_amount=transaction_result.send_amount,
        to_token_amount=transaction_result.receive_amount,
        price=transaction_result.price,
        buy_order_id=request.order_id,
    )

    return SellTokensResponse(
        id=result.id,
        created=result.created,
        status=OrderStatus.OK,
        token=result.to_token.name,
        action=OrderAction.SELL,
        amount=result.to_token_amount,
        price=result.price,
        buy_order_id=result.buy_order_id,
    )


@router.get(
    "/{pair_id}",
    response_model=list[BuyTokensResponse],
)
async def get_orders(
    pair_id: int,
    db_session: AsyncSession = Depends(get_session),
):
    order_buy_repository = OrderBuyRepository(db_session)
    pairs_repository = PairsRepository(db_session)
    # TODO: Refactor add relationships to Trade pair
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )
    token_id = pair.to_token.id
    result = await order_buy_repository.get_orders_for_token(
        token_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Orders not found",
        )

    result = [
        BuyTokensResponse(
            id=order.id,
            created=order.created,
            status=OrderStatus.OK,
            token=order.to_token.name,
            action=OrderAction.BUY,
            amount=order.to_token_amount / order.to_token.decimals,
            price=order.price,
            sells=[
                SellOrderDetails(
                    id=sell.id,
                    created=sell.created,
                    price=sell.price,
                    amount=sell.to_token_amount / sell.to_token.decimals,
                )
                for sell in order.sells
            ],
        )
        for order in result
    ]

    return result
