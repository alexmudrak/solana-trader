from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from brokers.jupiter_market import JupiterMarket
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
    broker_service = JupiterMarket()
    wallet = WalletService()

    pair_id = request.pair_id
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    last_price = await price_repository.get_latest(pair.to_token_id)
    buy_price_with_fee = last_price * MARKET_FEE

    from_token = pair.from_token
    to_token = pair.to_token
    required_token_amount = int(
        buy_price_with_fee * from_token.decimals * request.amount
    )
    receive_token_amount = int(pair.to_token.decimals * request.amount)

    # Make swap transaction
    dex_quote = await broker_service.get_quote_tokens(
        from_token.address,
        to_token.address,
        required_token_amount,
    )
    dex_receive_amount = int(dex_quote["outAmount"])
    dex_send_amount = int(dex_quote["inAmount"])
    dex_swap_value = float(dex_quote["swapUsdValue"])

    if dex_receive_amount < receive_token_amount:
        logger.critical(
            "Received amount from DEX is less than expected. "
            f"Get: {dex_receive_amount} expect: {receive_token_amount}"
        )
        return

    if dex_swap_value > (buy_price_with_fee * request.amount):
        logger.critical("Spend more than expected")
        return

    dex_transaction_instructions = await broker_service.make_transaction(
        dex_quote, str(wallet.pub_key)
    )

    # Check wallet balance
    base_token_balance = await wallet.get_balance(from_token)
    if (
        not base_token_balance.token
        or required_token_amount > base_token_balance.token.amount
    ):
        logger.warning(
            "Insufficient balance for buying. "
            f"Required: {required_token_amount}, "
            f"Available: {base_token_balance.token.amount if base_token_balance.token else 0}"
        )
        return

    # Send transaction
    await wallet.send_transaction(dex_transaction_instructions)

    from_token_amount = dex_send_amount
    to_token_amount = dex_receive_amount

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

    broker_service = JupiterMarket()
    wallet = WalletService()

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

    from_token = pair.to_token
    to_token = pair.from_token
    required_token_amount = int(order.to_token_amount)
    receive_token_amount = int(
        sell_price_with_fee * request.amount * to_token.decimals
    )

    # Make swap transaction
    dex_quote = await broker_service.get_quote_tokens(
        from_token.address,
        to_token.address,
        required_token_amount,
    )

    dex_transaction_instructions = await broker_service.make_transaction(
        dex_quote, str(wallet.pub_key)
    )

    dex_receive_amount = int(dex_quote["outAmount"])
    dex_send_amount = int(dex_quote["inAmount"])

    if dex_receive_amount < receive_token_amount:
        logger.critical(
            "Received amount from DEX is less than expected. "
            f"Get: {dex_receive_amount} expect: {receive_token_amount}"
        )
        return

    # Check wallet balance
    base_token_balance = await wallet.get_balance(to_token)
    if (
        not base_token_balance.token
        or required_token_amount > base_token_balance.amount
    ):
        logger.warning(
            "Insufficient balance for selling. "
            f"Required: {required_token_amount}, "
            f"Available: {base_token_balance.amount if base_token_balance.token else 0}"
        )
        return

    # Send transaction
    await wallet.send_transaction(dex_transaction_instructions)

    from_token_amount = int(dex_send_amount)
    to_token_amount = int(dex_receive_amount)

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
