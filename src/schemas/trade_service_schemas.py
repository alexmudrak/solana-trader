from datetime import datetime

from pydantic import BaseModel


class PriceByMinute(BaseModel):
    time: datetime
    value: float
