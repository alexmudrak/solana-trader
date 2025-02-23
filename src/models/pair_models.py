from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseAppModel
from models.token_models import Token


class TradingPairSettings(BaseAppModel):
    __tablename__ = "trading_pair_settings"

    from_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    from_token: Mapped[Token] = relationship(
        Token,
        foreign_keys=[from_token_id],
    )
    to_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"), nullable=False
    )
    to_token: Mapped[Token] = relationship(
        Token,
        foreign_keys=[to_token_id],
    )
    data_fetch_frequency: Mapped[float] = mapped_column(
        Float(),
        nullable=False,
    )
    trading_setting_id: Mapped[int] = mapped_column(
        ForeignKey("trading_settings.id")
    )
    trading_setting: Mapped["TradingSettings"] = relationship(
        "TradingSettings",
        back_populates="trading_pairs",
    )


class TradingSettings(BaseAppModel):
    __tablename__ = "trading_settings"

    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
    )
    trading_pairs: Mapped[list[TradingPairSettings]] = relationship(
        "TradingPairSettings",
        back_populates="trading_setting",
    )
