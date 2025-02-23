from sqlalchemy.ext.asyncio import AsyncSession

from models.orders_models import OrderSell


class OrderSellRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        price: float,
        buy_order_id: int,
    ) -> OrderSell:
        obj = OrderSell(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            price=price,
            buy_order_id=buy_order_id,
        )
        self.session.add(obj)
        await self.session.flush()

        return obj
