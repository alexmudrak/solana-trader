from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.pair_models import TradingSettings
from schemas.pairs_schemas import UpdatePairSettingsRequest


class PairsSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pairs_settings(self) -> list[TradingSettings]:
        stmt = select(TradingSettings)
        result = await self.session.execute(stmt)
        pairs_settings = result.scalars().all()

        return list(pairs_settings)

    async def create(self, name: str) -> TradingSettings:
        obj = TradingSettings(
            name=name,
        )
        self.session.add(obj)
        await self.session.flush()

        return obj

    async def update_settings(
        self,
        pair_id: int,
        settings_data: UpdatePairSettingsRequest,
    ) -> TradingSettings:
        stmt = select(TradingSettings).where(TradingSettings.id == pair_id)
        result = await self.session.execute(stmt)
        obj = result.scalars().first()

        if not obj:
            raise ValueError(f"No trading settings found for ID: {pair_id}")

        obj.take_profit_percentage = settings_data.take_profit_percentage
        obj.stop_loss_percentage = settings_data.stop_loss_percentage
        obj.short_ema_time_period = settings_data.short_ema_time_period
        obj.long_ema_time_period = settings_data.long_ema_time_period
        obj.rsi_buy_threshold = settings_data.rsi_buy_threshold
        obj.rsi_sell_threshold = settings_data.rsi_sell_threshold
        obj.rsi_time_period = settings_data.rsi_time_period
        obj.buy_amount = settings_data.buy_amount
        obj.buy_max_orders_threshold = settings_data.buy_max_orders_threshold
        await self.session.flush()

        return obj
