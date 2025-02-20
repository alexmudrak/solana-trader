from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from core.constants import OrderAction
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


class Order(BaseAppModel):
    __tablename__ = "orders"

    from_token: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    to_token: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    action: Mapped[OrderAction] = mapped_column(
        String(4),
        nullable=False,
    )
