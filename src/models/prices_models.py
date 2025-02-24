from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import Token
from models.base import BaseAppModel


class Price(BaseAppModel):
    __tablename__ = "prices"

    token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    token: Mapped[Token] = relationship("Token", foreign_keys=[token_id])
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
