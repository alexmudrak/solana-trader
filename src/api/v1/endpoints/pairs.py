import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repositories.pairs_repository import PairsRepository
from repositories.pairs_settings_repository import PairsSettingsRepository
from schemas.pairs_schemas import (
    ChangeIsActivePairsRequest,
    CreatePairsRequest,
    CreatePairsSettingsRequest,
    PairsResponse,
    PairsSettingsResponse,
    UpdatePairSettingsRequest,
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
    pairs_settings_repository = PairsSettingsRepository(db_session)

    trading_setting = await pairs_settings_repository.create(
        f"Setting {time.time()}"
    )
    result = await pairs_repository.create(
        request.from_token_id,
        request.to_token_id,
        trading_setting.id,
    )

    return result


@router.patch("/change_active/{pair_id}", response_model=PairsResponse)
async def change_active_pairs(
    pair_id,
    request: ChangeIsActivePairsRequest,
    db_session: AsyncSession = Depends(get_session),
):
    pairs_repository = PairsRepository(db_session)

    result = await pairs_repository.update_active(
        pair_id,
        request.is_active,
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


@router.patch(
    "/settings/{pair_id}",
    response_model=PairsSettingsResponse,
)
async def update_settings(
    pair_id: int,
    request: UpdatePairSettingsRequest,
    db_session: AsyncSession = Depends(get_session),
):
    pairs_repository = PairsRepository(db_session)
    pairs_settings_repository = PairsSettingsRepository(db_session)

    pair = await pairs_repository.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Trade pair id {pair_id} not found",
        )

    result = await pairs_settings_repository.update_settings(
        pair.trading_setting_id, request
    )

    return result
