import asyncio

from brokers.jupiter_market import JupiterMarket
from core.constants import Token
from core.database import get_session
from core.settings import settings
from models.pair_models import TradingPairSettings
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.pairs_repository import PairsRepository
from repositories.prices_repository import PricesRepository
from services.trade_service import TradeService


async def get_latest_price(pairs_settings: list[TradingPairSettings]):
    async for session in get_session():
        prices_repository = PricesRepository(session)

        market = JupiterMarket()
        to_tokens_list = [
            pair_setting.to_token.address for pair_setting in pairs_settings
        ]
        # TODO: Change when can add different pairs not
        #       only USDC -> TOKEN
        #       Need to remove
        from_token = Token.USDC

        result = await market.get_price(
            to_tokens_list,
            from_token.value,
        )
        for pair_setting in pairs_settings:
            to_token = pair_setting.to_token
            price = float(result["data"][to_token.address]["price"])

            await prices_repository.create(price, to_token.id)

            print(
                f"[FETCHER] Current WITHOUT FEE price for {from_token.name} to {to_token.name}: {price:.2f}"
            )


async def trade_execution(pairs_settings: list[TradingPairSettings]):
    for pair_settings in pairs_settings:
        async for session in get_session():
            prices_repository = PricesRepository(session)
            orders_buy_repository = OrderBuyRepository(session)
            orders_sell_repository = OrderSellRepository(session)

            trader = TradeService(
                pair_settings,
                prices_repository,
                orders_buy_repository,
                orders_sell_repository,
            )

            await trader.check_sell_orders()
            await trader.check_buy_order()


async def run_background_processes():
    all_active_pairs = []
    while True:
        async for session in get_session():
            pairs_repository = PairsRepository(session)
            all_active_pairs = await pairs_repository.get_pairs(
                only_active=True
            )
        try:
            await get_latest_price(all_active_pairs)
            await trade_execution(all_active_pairs)
        except Exception as e:
            print(f"Error fetching price: {e}")

        await asyncio.sleep(settings.app_fetch_price_sleep)
