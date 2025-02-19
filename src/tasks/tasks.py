import asyncio
from datetime import datetime

from brokers.jupiter_market import JupiterMarket
from core.constants import Token
from core.database import get_session
from models.prices_models import Price


async def get_prices_background(from_token: Token, to_token: Token):
    market = JupiterMarket()
    while True:
        try:
            session = await get_session().__anext__()
            async with session:
                result = await market.get_price(
                    from_token.value, to_token.value
                )

                price = float(result["data"][from_token.value]["price"])

                new_price = Price(
                    token_name=from_token.name,
                    price=price,
                    timestamp=datetime.now().timestamp(),
                )
                session.add(new_price)
                await session.commit()
            print(f"Current Price 1: {from_token} to {to_token} - {price}")
        except Exception as e:
            print(f"Error fetching price: {e}")
        await asyncio.sleep(5)
