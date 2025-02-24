from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.prices_models import Price


class PricesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, token_id: int) -> float:
        stmt = (
            select(Price)
            .where(Price.token_id == token_id)
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
        self,
        token_id: int,
        time_threshold: datetime,
        descending: bool = False,
    ) -> list[Price]:
        stmt = select(Price).where(
            Price.token_id == token_id,
            Price.created >= time_threshold,
        )
        if descending:
            stmt = stmt.order_by(Price.created.desc())
        else:
            stmt = stmt.order_by(Price.created)

        result = await self.session.execute(stmt)
        recent_prices = list(result.scalars().all())

        return recent_prices

    async def create(
        self,
        price: float,
        token_id: int,
    ) -> Price:
        obj = Price(
            token_id=token_id,
            price=price,
            created=datetime.now(UTC),
        )
        self.session.add(obj)
        await self.session.flush()

        return obj
