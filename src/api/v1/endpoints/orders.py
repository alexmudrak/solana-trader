from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import MARKET_FEE
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

router = APIRouter()


@router.post("/buy", response_model=BuyTokensResponse)
async def buy_tokens(
    request: BuyTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    order_buy_repository = OrderBuyRepository(db_session)
    pairs_repository = PairsRepository(db_session)
    price_repository = PricesRepository(db_session)

    pair_id = request.pair_id
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    last_price = await price_repository.get_latest(pair.to_token_id)
    buy_price_with_fee = last_price / MARKET_FEE
    # TODO: Calculate from swap transaction
    from_token_amount = int(
        buy_price_with_fee * pair.from_token.decimals * request.amount
    )
    to_token_amount = int(request.amount * pair.to_token.decimals)

    # TODO: Add swap transaction
    result = await order_buy_repository.create(
        from_token_id=pair.from_token_id,
        to_token_id=pair.to_token_id,
        from_token_amount=from_token_amount,
        to_token_amount=to_token_amount,
        price=buy_price_with_fee,
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
    sell_price_with_fee = last_price / MARKET_FEE
    from_token_amount = int(order.to_token_amount)
    # TODO: Calculate from swap transaction
    to_token_amount = int(order.from_token_amount)

    # TODO: Add swap transaction
    result = await order_sell_repository.create(
        from_token_id=pair.to_token_id,
        to_token_id=pair.from_token_id,
        from_token_amount=from_token_amount,
        to_token_amount=to_token_amount,
        price=sell_price_with_fee,
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
