import asyncio

from loguru import logger

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
from utils.trade_indicators import TradeIndicators


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

            logger.opt(colors=True).log(
                "FETCHER",
                f"Current <red>WITHOUT FEE</red> price for <underline><b>{from_token.name}</b></underline> to <underline><b>{to_token.name}</b></underline>: <white>{price:.2f}</white>",
            )


async def trade_execution(pairs_settings: list[TradingPairSettings]):
    trade_indicators = TradeIndicators()
    for pair_settings in pairs_settings:
        async for session in get_session():
            prices_repository = PricesRepository(session)
            orders_buy_repository = OrderBuyRepository(session)
            orders_sell_repository = OrderSellRepository(session)

            trader = TradeService(
                trade_indicators,
                pair_settings,
                prices_repository,
                orders_buy_repository,
                orders_sell_repository,
            )
            await trader.analyzer()


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
            logger.error(f"Error fetching price: {e}")

        await asyncio.sleep(settings.app_fetch_price_sleep)
