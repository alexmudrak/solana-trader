from pydantic import BaseModel, Field


class BuyTokensRequest(BaseModel):
    token_select: str = Field(..., alias="token-select")
    amount: float
