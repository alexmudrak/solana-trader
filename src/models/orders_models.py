from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseAppModel
from models.token_models import Token


class OrderBuy(BaseAppModel):
    __tablename__ = "orders_buy"

    from_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    from_token: Mapped[Token] = relationship(
        "Token", foreign_keys=[from_token_id]
    )
    to_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    to_token: Mapped[Token] = relationship(
        "Token",
        foreign_keys=[to_token_id],
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

    from_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    from_token: Mapped["Token"] = relationship(
        "Token", foreign_keys=[from_token_id]
    )
    to_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    to_token: Mapped["Token"] = relationship(
        "Token", foreign_keys=[to_token_id]
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
