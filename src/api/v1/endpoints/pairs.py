from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repositories.pairs_repository import PairsRepository
from repositories.pairs_settings_repository import PairsSettingsRepository
from schemas.pairs_schemas import (
    CreatePairsRequest,
    CreatePairsSettingsRequest,
    PairsResponse,
    PairsSettingsResponse,
)

router = APIRouter()


@router.get("/", response_model=list[PairsResponse])
async def get_pairs(
    db_session: AsyncSession = Depends(get_session),
):
    pairs_repository = PairsRepository(db_session)

    result = await pairs_repository.get_pairs()

    return result


@router.post("/", response_model=PairsResponse)
async def create_pairs(
    request: CreatePairsRequest,
    db_session: AsyncSession = Depends(get_session),
):
    # TODO: Change when can add different pairs not
    #       only USDC -> TOKEN
    request.from_token_id = 1
    pairs_repository = PairsRepository(db_session)

    result = await pairs_repository.create(
        request.from_token_id,
        request.to_token_id,
        request.trading_setting_id,
    )

    return result


@router.get("/settings", response_model=list[PairsSettingsResponse])
async def get_pairs_settings(
    db_session: AsyncSession = Depends(get_session),
):
    pairs_settings_repository = PairsSettingsRepository(db_session)

    result = await pairs_settings_repository.get_pairs_settings()

    return result


@router.post("/settings", response_model=PairsSettingsResponse)
async def create_pairs_settings(
    request: CreatePairsSettingsRequest,
    db_session: AsyncSession = Depends(get_session),
):
    pairs_settings_repository = PairsSettingsRepository(db_session)

    result = await pairs_settings_repository.create(request.name)

    return result
