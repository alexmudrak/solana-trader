from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.pair_models import TradingPairSettings


class PairsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pair_by_id(self, pair_id: int) -> TradingPairSettings | None:
        stmt = (
            select(TradingPairSettings)
            .options(
                selectinload(TradingPairSettings.from_token),
                selectinload(TradingPairSettings.to_token),
                selectinload(TradingPairSettings.trading_setting),
            )
            .where(TradingPairSettings.id == pair_id)
        )

        result = await self.session.execute(stmt)
        pair = result.scalars().one_or_none()

        return pair

    async def get_pairs(
        self, only_active: bool | None = None
    ) -> list[TradingPairSettings]:
        stmt = select(TradingPairSettings).options(
            selectinload(TradingPairSettings.from_token),
            selectinload(TradingPairSettings.to_token),
            selectinload(TradingPairSettings.trading_setting),
        )
        if only_active is True:
            stmt = stmt.where(
                TradingPairSettings.is_active == True  # noqa: E712
            )
        elif only_active is False:
            stmt = stmt.where(
                TradingPairSettings.is_active == False  # noqa: E712
            )

        result = await self.session.execute(stmt)
        pairs = result.scalars().all()

        return list(pairs)

    async def create(
        self,
        from_token_id: int,
        to_token_id: int,
        data_fetch_frequency: float,
        trading_setting_id: int,
    ) -> TradingPairSettings:
        obj = TradingPairSettings(
            from_token_id=from_token_id,
            to_token_id=to_token_id,
            data_fetch_frequency=data_fetch_frequency,
            trading_setting_id=trading_setting_id,
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(
            obj,
            attribute_names=[
                "from_token",
                "to_token",
                "trading_setting",
            ],
        )

        return obj
