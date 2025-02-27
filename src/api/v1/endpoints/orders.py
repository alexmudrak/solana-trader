from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.pairs_repository import PairsRepository
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
    pair_id = request.pair_id
    # TODO: Refactor add relationships to Trade pair
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    # TODO: Add order fee
    result = await order_buy_repository.create(
        from_token_id=pair.from_token_id,
        to_token_id=pair.to_token_id,
        amount=request.amount,
        price=request.price,
    )

    return BuyTokensResponse(
        id=result.id,
        created=result.created,
        status=OrderStatus.OK,
        token=result.to_token.name,
        action=OrderAction.BUY,
        amount=result.amount,
        price=result.price,
    )


@router.post("/sell", response_model=SellTokensResponse)
async def sell_tokens(
    request: SellTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    order_sell_repository = OrderSellRepository(db_session)
    pairs_repository = PairsRepository(db_session)
    pair_id = request.pair_id
    # TODO: Refactor add relationships to Trade pair
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    # TODO: Add order fee
    result = await order_sell_repository.create(
        from_token_id=pair.to_token_id,
        to_token_id=pair.from_token_id,
        amount=request.amount,
        price=request.price,
        buy_order_id=request.order_id,
    )

    return SellTokensResponse(
        id=result.id,
        created=result.created,
        status=OrderStatus.OK,
        token=result.to_token.name,
        action=OrderAction.SELL,
        amount=result.amount,
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
            amount=order.amount,
            price=order.price,
            sells=[
                SellOrderDetails(
                    id=sell.id,
                    created=sell.created,
                    price=sell.price,
                    amount=sell.amount,
                )
                for sell in order.sells
            ],
        )
        for order in result
    ]

    return result
