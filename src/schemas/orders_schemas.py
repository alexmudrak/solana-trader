from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class OrderStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class OrderAction(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderBase(BaseModel):
    id: int
    created: datetime
    status: OrderStatus
    token: str
    action: OrderAction
    amount: float
    price: float


class SellOrderDetails(BaseModel):
    id: int
    created: datetime
    price: float
    amount: float


class BuyTokensResponse(OrderBase):
    sells: list[SellOrderDetails] = []


class SellTokensResponse(OrderBase):
    buy_order_id: int
