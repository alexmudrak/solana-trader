from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import Token
from models.base import BaseAppModel


class Price(BaseAppModel):
    __tablename__ = "prices"

    from_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    from_token: Mapped[Token] = relationship(
        "Token", foreign_keys=[from_token_id]
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
