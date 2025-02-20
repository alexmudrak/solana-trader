from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.constants import MAIN_TOKEN, OrderAction
from core.database import get_session
from models.orders_models import OrderBuy, OrderSell
from models.prices_models import Price
from schemas.tokens_schemas import BuyTokensRequest, SellTokensRequest

router = APIRouter()


@router.get("/", response_class=JSONResponse)
async def get_tokens(
    db_session: AsyncSession = Depends(get_session),
):
    result = await db_session.execute(select(Price.token_name).distinct())

    tokens = result.scalars().all()

    return {"tokens": tokens}


@router.get("/prices/{token_name}", response_class=JSONResponse)
async def get_prices_data(
    token_name: str,
    db_session: AsyncSession = Depends(get_session),
):
    result = await db_session.execute(
        select(Price)
        .where(Price.token_name == token_name)
        .order_by(Price.created)
    )
    prices_data = result.scalars().all()

    if not prices_data:
        raise HTTPException(
            status_code=404,
            detail="Token not found",
        )

    prices = {"created": [], "prices": []}
    for price in prices_data:
        prices["created"].append(price.created)
        prices["prices"].append(price.price)

    return prices


@router.post("/buy", response_class=JSONResponse)
async def buy_tokens(
    request: BuyTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    async with db_session.begin():
        order = OrderBuy(
            from_token=MAIN_TOKEN,
            to_token=request.token_select,
            amount=request.amount,
            price=request.amount * request.price,
        )
        db_session.add(order)
        await db_session.flush()

    return {
        "id": order.id,
        "status": "OK",
        "token": order.to_token,
        "action": OrderAction.BUY,
        "amount": order.amount,
        "price": order.price,
    }


@router.post("/sell", response_class=JSONResponse)
async def sell_tokens(
    request: SellTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    async with db_session.begin():
        order = OrderSell(
            from_token=request.token_select,
            to_token=MAIN_TOKEN,
            amount=request.amount,
            price=request.amount * request.price,
            buy_order_id=request.order_id,
        )
        db_session.add(order)
        await db_session.flush()

    return {
        "status": "OK",
        "token": order.to_token,
        "action": OrderAction.SELL,
        "amount": order.amount,
        "price": order.price,
    }


@router.get("/orders/{token_name}", response_class=JSONResponse)
async def get_orders(
    token_name: str,
    db_session: AsyncSession = Depends(get_session),
):
    result = await db_session.execute(
        select(OrderBuy)
        .options(selectinload(OrderBuy.sells))
        .where(OrderBuy.to_token == token_name)
        .order_by(OrderBuy.created.desc())
    )
    orders_data = result.scalars().all()
    if not orders_data:
        raise HTTPException(
            status_code=404,
            detail="Orders not found",
        )
    result = [
        {
            "id": order.id,
            "date": order.created,
            "token": order.to_token,
            "count": order.amount,
            "price": order.price,
            "sells": order.sells,
        }
        for order in orders_data
    ]

    return result
