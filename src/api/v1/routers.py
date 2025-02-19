from fastapi import APIRouter

from api.v1.endpoints import tokens

router = APIRouter()

router.include_router(tokens.router, tags=["Tokens"], prefix="/tokens")
