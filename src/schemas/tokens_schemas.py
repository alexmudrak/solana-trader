from datetime import datetime

from pydantic import BaseModel, Field


class BuyTokensRequest(BaseModel):
    token_select: str = Field(..., alias="token-select")
    amount: float
    price: float = Field(..., alias="current-price-value")


class SellTokensRequest(BuyTokensRequest):
    order_id: int = Field(..., alias="order-id")


class TokensResponse(BaseModel):
    tokens: list[str]


class PriceResponse(BaseModel):
    created: list[datetime]
    prices: list[float]
