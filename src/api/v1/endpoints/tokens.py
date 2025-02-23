from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repositories.tokens_repository import TokensRepository
from schemas.tokens_schemas import (
    TokenRequest,
    TokenResponse,
)

router = APIRouter()


@router.get("/", response_model=list[TokenResponse])
async def get_tokens(
    db_session: AsyncSession = Depends(get_session),
):
    prices_repository = TokensRepository(db_session)

    result = await prices_repository.get_tokens()

    return result


@router.post("/", response_model=TokenResponse)
async def create_token(
    request: TokenRequest,
    db_session: AsyncSession = Depends(get_session),
):
    tokens_repository = TokensRepository(db_session)

    result = await tokens_repository.create(
        request.name,
        request.address,
    )

    return result
