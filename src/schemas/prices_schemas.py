from datetime import datetime

from pydantic import BaseModel


class PriceResponse(BaseModel):
    created: list[datetime]
    prices: list[float]
