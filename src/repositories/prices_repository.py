from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.prices_models import Price


class PricesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, token_name: str) -> float:
        stmt = (
            select(Price)
            .where(Price.token_name == token_name)
            .order_by(Price.created.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        latest_price = result.scalars().first()

        if latest_price:
            return latest_price.price
        else:
            raise Exception("No prices found for the specified token.")

    async def get_recent_prices(
        self, token_name: str, time_threshold: datetime
    ) -> list[Price]:
        stmt = (
            select(Price)
            .where(
                Price.token_name == token_name,
                Price.created >= time_threshold,
            )
            .order_by(Price.created.desc())
        )
        result = await self.session.execute(stmt)
        recent_prices = list(result.scalars().all())

        return recent_prices

    async def create(
        self,
        price: float,
        token_name: str,
    ) -> float:
        async with self.session.begin():
            obj = Price(
                token_name=token_name,
                price=price,
                created=datetime.now(UTC),
            )
            self.session.add(obj)
            await self.session.commit()

        return obj.price
