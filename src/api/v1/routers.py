from fastapi import APIRouter

from api.v1.endpoints import orders, tokens

router = APIRouter()

router.include_router(tokens.router, tags=["Tokens"], prefix="/tokens")
router.include_router(orders.router, tags=["Orders"], prefix="/orders")
