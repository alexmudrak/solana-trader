from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.pair_models import TradingSettings


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
