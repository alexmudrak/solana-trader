import asyncio

from brokers.jupiter_market import JupiterMarket
from core.constants import Token
from core.database import get_session
from core.settings import settings
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.prices_repository import PricesRepository
from services.trade_service import TradeService


async def get_latest_price():
    async for session in get_session():
        prices_repository = PricesRepository(session)

        market = JupiterMarket()
        from_token = Token.SOL
        to_token = Token.USDC

        result = await market.get_price(from_token.value, to_token.value)
        price = float(result["data"][from_token.value]["price"])

        await prices_repository.create(price, from_token.name)

        print(
            f"[FETCHER] Current WITHOUT FEE price for {from_token} to {to_token}: {price:.2f}"
        )

        return price


async def trade_execution():
    async for session in get_session():
        prices_repository = PricesRepository(session)
        orders_buy_repository = OrderBuyRepository(session)
        orders_sell_repository = OrderSellRepository(session)

        trader = TradeService(
            prices_repository,
            orders_buy_repository,
            orders_sell_repository,
        )

        await trader.check_sell_orders()
        await trader.check_buy_order()


async def run_background_processes():
    while True:
        try:
            await get_latest_price()
            await trade_execution()
        except Exception as e:
            print(f"Error fetching price: {e}")

        await asyncio.sleep(settings.app_fetch_price_sleep)
