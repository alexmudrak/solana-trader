from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import MAIN_TOKEN, OrderAction
from core.database import get_session
from models.prices_models import Order, Price
from schemas.tokens_schemas import BuyTokensRequest

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
        order = Order(
            from_token=MAIN_TOKEN,
            to_token=request.token_select,
            action=OrderAction.BUY.value,
            amount=request.amount,
            price=request.amount * request.price,
        )
        db_session.add(order)
        await db_session.flush()

    return {
        "status": "OK",
        "token": order.to_token,
        "action": OrderAction.BUY,
        "amount": order.amount,
        "price": order.price,
    }


@router.post("/sell", response_class=JSONResponse)
async def sell_tokens(
    request: BuyTokensRequest,
    db_session: AsyncSession = Depends(get_session),
):
    async with db_session.begin():
        order = Order(
            from_token=request.token_select,
            to_token=MAIN_TOKEN,
            action=OrderAction.SELL.value,
            amount=request.amount,
            price=request.amount * request.price,
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
        select(Order)
        .where(
            (
                (Order.to_token == token_name)
                & (Order.action == OrderAction.BUY.value)
            )
            | (
                (Order.from_token == token_name)
                & (Order.action == OrderAction.SELL.value)
            )
        )
        .order_by(Order.created.desc())
    )
    orders_data = result.scalars().all()
    if not orders_data:
        raise HTTPException(
            status_code=404,
            detail="Orders not found",
        )
    result = [
        {
            "date": order.created,
            "token": order.to_token,
            "count": order.amount,
            "price": order.price,
            "action": order.action,
        }
        for order in orders_data
    ]
    return result
