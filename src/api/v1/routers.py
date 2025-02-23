from fastapi import APIRouter

from api.v1.endpoints import orders, pairs, prices, tokens

router = APIRouter()

router.include_router(prices.router, tags=["Prices"], prefix="/prices")
router.include_router(tokens.router, tags=["Tokens"], prefix="/tokens")
router.include_router(orders.router, tags=["Orders"], prefix="/orders")
router.include_router(pairs.router, tags=["Trading pairs"], prefix="/pairs")
