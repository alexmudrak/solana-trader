from pydantic import BaseModel


class BuyTokensRequest(BaseModel):
    token_select: int
    amount: float
    price: float


class SellTokensRequest(BuyTokensRequest):
    order_id: int


class TokenRequest(BaseModel):
    name: str
    address: str


class TokenResponse(BaseModel):
    id: int
    name: str
    address: str

    class Config:
        from_attributes = True
