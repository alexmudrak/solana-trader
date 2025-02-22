from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders_models import OrderBuy


class OrderBuyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_opened_orders(self) -> list[OrderBuy]:
        stmt = (
            select(OrderBuy)
            .outerjoin(OrderBuy.sells)
            .where(OrderBuy.sells == None)  # noqa: E711
        )
        result = await self.session.execute(stmt)
        orders = list(result.scalars().all())

        return orders

    async def create(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        price: float,
    ) -> OrderBuy:
        async with self.session:
            obj = OrderBuy(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                price=price,
            )
            self.session.add(obj)
            await self.session.commit()

        return obj
