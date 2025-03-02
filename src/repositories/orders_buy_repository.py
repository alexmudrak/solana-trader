from datetime import datetime

from loguru import logger
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
                .options(
                    selectinload(OrderBuy.sells),
                    selectinload(OrderBuy.from_token),
                    selectinload(OrderBuy.to_token),
                )
                .where(OrderBuy.sells == None)  # noqa: E711
            )
            result = await self.session.execute(stmt)
            orders = list(result.scalars().all())

            return orders
        except SQLAlchemyError as e:
            logger.warning(f"Error while fetching opened orders: {e}")
            return []

    async def get_orders_for_token(
        self,
        token_id: int,
    ) -> list[OrderBuy]:
        try:
            stmt = (
                select(OrderBuy)
                .options(selectinload(OrderBuy.sells))
                .where(OrderBuy.to_token_id == token_id)
                .order_by(OrderBuy.created.desc())
            )
            result = await self.session.execute(stmt)
            orders = list(result.scalars().all())

            return orders
        except SQLAlchemyError as e:
            logger.warning(
                f"Error while fetching orders for token {token_id}: {e}"
            )
            return []

    async def get_recent_orders_count(
        self, token_id: int, time_threshold: datetime
    ) -> int:
        try:
            stmt = select(func.count(OrderBuy.id)).where(
                OrderBuy.to_token_id == token_id,
                OrderBuy.created >= time_threshold,
            )
            result = await self.session.execute(stmt)
            count = result.scalar()

            return count or 0
        except SQLAlchemyError as e:
            logger.warning(f"Error fetching order count: {e}")
            return 0

    async def create(
        self,
        from_token_id: int,
        to_token_id: int,
        from_token_amount: int,
        to_token_amount: int,
        price: float,
    ) -> OrderBuy:
        obj = OrderBuy(
            from_token_id=from_token_id,
            to_token_id=to_token_id,
            from_token_amount=from_token_amount,
            to_token_amount=to_token_amount,
            price=price,
        )
        self.session.add(obj)
        await self.session.flush()

        return obj
