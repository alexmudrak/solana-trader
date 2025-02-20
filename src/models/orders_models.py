from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseAppModel


class OrderBuy(BaseAppModel):
    __tablename__ = "orders_buy"

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
    sells: Mapped[list["OrderSell"]] = relationship(
        "OrderSell", back_populates="buy_order"
    )


class OrderSell(BaseAppModel):
    __tablename__ = "orders_sell"

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
    buy_order_id: Mapped[int] = mapped_column(
        ForeignKey("orders_buy.id"), nullable=False
    )
    buy_order: Mapped[OrderBuy] = relationship(
        "OrderBuy", back_populates="sells"
    )
