from pydantic import BaseModel


class BuyTokensRequest(BaseModel):
    pair_id: int
    amount: float


class SellTokensRequest(BuyTokensRequest):
    order_id: int


class TokenRequest(BaseModel):
    name: str
    address: str
    decimals: int


class TokenResponse(BaseModel):
    id: int
    name: str
    address: str

    class Config:
        from_attributes = True
