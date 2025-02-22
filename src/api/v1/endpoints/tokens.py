from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repositories.prices_repository import PricesRepository
from schemas.tokens_schemas import (
    PriceResponse,
    TokensResponse,
)

router = APIRouter()


@router.get("/", response_model=TokensResponse)
async def get_tokens(
    db_session: AsyncSession = Depends(get_session),
):
    prices_repository = PricesRepository(db_session)

    result = await prices_repository.get_tokens()

    return TokensResponse(tokens=result)


@router.get("/prices/{token_name}", response_model=PriceResponse)
async def get_prices_data(
    token_name: str,
    minutes: int = 60 * 24,
    db_session: AsyncSession = Depends(get_session),
):
    prices_repository = PricesRepository(db_session)
    time_threshold = datetime.now(UTC) - timedelta(minutes=minutes)

    result = await prices_repository.get_recent_prices(
        token_name,
        time_threshold,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Token not found",
        )

    prices = PriceResponse(
        created=[price.created for price in result],
        prices=[price.price for price in result],
    )

    return prices
