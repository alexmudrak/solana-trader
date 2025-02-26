from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repositories.pairs_repository import PairsRepository
from repositories.prices_repository import PricesRepository
from schemas.prices_schemas import PriceResponse

router = APIRouter()


@router.get("/{pair_id}", response_model=PriceResponse)
async def get_prices_data(
    pair_id: int,
    minutes: int = 60 * 3,
    db_session: AsyncSession = Depends(get_session),
):
    # TODO: Refactor add relationships to Trade pair
    prices_repository = PricesRepository(db_session)
    pairs_repository = PairsRepository(db_session)

    time_threshold = datetime.now(UTC) - timedelta(minutes=minutes)
    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    token_id = pair.to_token.id
    result = await prices_repository.get_recent_prices(
        token_id,
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
