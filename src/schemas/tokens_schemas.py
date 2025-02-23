from pydantic import BaseModel, Field


class BuyTokensRequest(BaseModel):
    token_select: str = Field(..., alias="token-select")
    amount: float
    price: float = Field(..., alias="current-price-value")


class SellTokensRequest(BuyTokensRequest):
    order_id: int = Field(..., alias="order-id")


class TokenRequest(BaseModel):
    name: str
    address: str


class TokenResponse(BaseModel):
    id: int
    name: str
    address: str

    class Config:
        from_attributes = True
