from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseAppModel


class Token(BaseAppModel):
    __tablename__ = "tokens"

    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
    )
    address: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )
