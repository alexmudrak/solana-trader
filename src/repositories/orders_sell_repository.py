from sqlalchemy.ext.asyncio import AsyncSession

from models.orders_models import OrderSell


class OrderSellRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        from_token_id: int,
        to_token_id: int,
        from_token_amount: int,
        to_token_amount: int,
        price: float,
        buy_order_id: int,
    ) -> OrderSell:
        obj = OrderSell(
            from_token_id=from_token_id,
            to_token_id=to_token_id,
            from_token_amount=from_token_amount,
            to_token_amount=to_token_amount,
            price=price,
            buy_order_id=buy_order_id,
        )
        self.session.add(obj)
        await self.session.flush()

        return obj
