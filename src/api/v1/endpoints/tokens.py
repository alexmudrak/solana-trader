from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from models.prices_models import Price

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
        .order_by(Price.timestamp)
    )
    prices_data = result.scalars().all()

    if not prices_data:
        raise HTTPException(
            status_code=404,
            detail="Token not found",
        )

    prices = {"timestamps": [], "prices": []}
    for price in prices_data:
        prices["timestamps"].append(price.timestamp)
        prices["prices"].append(price.price)

    return prices
