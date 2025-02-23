from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.orders_models import OrderBuy


class OrderBuyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_opened_orders(self) -> list[OrderBuy]:
        try:
            stmt = (
                select(OrderBuy)
                .options(selectinload(OrderBuy.sells))
                .where(OrderBuy.sells == None)  # noqa: E711
            )
            result = await self.session.execute(stmt)
            orders = list(result.scalars().all())

            return orders
        except SQLAlchemyError as e:
            print(f"Error while fetching opened orders: {e}")
            return []

    async def get_orders_for_token(
        self,
        token_name: str,
    ) -> list[OrderBuy]:
        try:
            stmt = (
                select(OrderBuy)
                .options(selectinload(OrderBuy.sells))
                .where(OrderBuy.to_token == token_name)
                .order_by(OrderBuy.created.desc())
            )
            result = await self.session.execute(stmt)
            orders = list(result.scalars().all())

            return orders
        except SQLAlchemyError as e:
            print(f"Error while fetching orders for token {token_name}: {e}")
            return []

    async def get_recent_orders_count(
        self, token_name: str, time_threshold: datetime
    ) -> int:
        try:
            stmt = select(func.count(OrderBuy.id)).where(
                OrderBuy.to_token == token_name,
                OrderBuy.created >= time_threshold,
            )
            result = await self.session.execute(stmt)
            count = result.scalar()

            return count or 0
        except SQLAlchemyError as e:
            print(f"Error fetching order count: {e}")
            return 0

    async def create(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        price: float,
    ) -> OrderBuy:
        obj = OrderBuy(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            price=price,
        )
        self.session.add(obj)
        await self.session.flush()

        return obj
