from pydantic import BaseModel


class WalletTokenBalance(BaseModel):
    name: str
    amount: int


class WalletBalance(BaseModel):
    amount: int
    token: WalletTokenBalance | None = None
