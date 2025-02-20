from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseAppModel


class Price(BaseAppModel):
    __tablename__ = "prices"

    token_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
