from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseAppModel
from models.token_models import Token


class TradingPairSettings(BaseAppModel):
    __tablename__ = "trading_pair_settings"

    from_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=False,
    )
    to_token_id: Mapped[int] = mapped_column(
        ForeignKey("tokens.id"), nullable=False
    )
    trading_setting_id: Mapped[int] = mapped_column(
        ForeignKey("trading_settings.id")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    from_token: Mapped[Token] = relationship(
        Token,
        foreign_keys=[from_token_id],
    )
    to_token: Mapped[Token] = relationship(
        Token,
        foreign_keys=[to_token_id],
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
    take_profit_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.05,
    )
    stop_loss_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.05,
    )
    short_ema_time_period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )
    long_ema_time_period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
    )
    rsi_buy_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )
    rsi_sell_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
    )
    rsi_time_period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=14,
    )
    buy_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.1,
    )
    buy_max_orders_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )
    buy_max_orders_in_last_period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    buy_check_period_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )
    auto_buy_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    auto_sell_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    trading_pairs: Mapped[list[TradingPairSettings]] = relationship(
        "TradingPairSettings",
        back_populates="trading_setting",
    )
