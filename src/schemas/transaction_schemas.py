from pydantic import BaseModel


class TransactionResult(BaseModel):
    send_amount: int
    receive_amount: int
    price: float
