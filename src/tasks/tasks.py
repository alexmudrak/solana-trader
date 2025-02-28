import asyncio

from loguru import logger

from brokers.abstract_market import AbstractMarket
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
from services.wallet_service import WalletService
from utils.trade_indicators import TradeIndicators


async def get_latest_price(
    broker_service: AbstractMarket,
    pairs_settings: list[TradingPairSettings],
):
    async for session in get_session():
        prices_repository = PricesRepository(session)

        to_tokens_list = [
            pair_setting.to_token.address for pair_setting in pairs_settings
        ]
        # TODO: Change when can add different pairs not
        #       only USDC -> TOKEN
        #       Need to remove
        from_token = Token.USDC

        result = await broker_service.get_price(
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


async def trade_execution(
    wallet: WalletService,
    broker_service: AbstractMarket,
    pairs_settings: list[TradingPairSettings],
):
    trade_indicators = TradeIndicators()
    for pair_settings in pairs_settings:
        async for session in get_session():
            prices_repository = PricesRepository(session)
            orders_buy_repository = OrderBuyRepository(session)
            orders_sell_repository = OrderSellRepository(session)

            trader = TradeService(
                wallet,
                broker_service,
                trade_indicators,
                pair_settings,
                prices_repository,
                orders_buy_repository,
                orders_sell_repository,
            )
            await trader.analyzer()


async def run_background_processes():
    all_active_pairs = []
    broker_service = JupiterMarket()
    wallet_service = WalletService()

    while True:
        async for session in get_session():
            pairs_repository = PairsRepository(session)
            all_active_pairs = await pairs_repository.get_pairs(
                only_active=True
            )
        try:
            await get_latest_price(broker_service, all_active_pairs)
            await trade_execution(
                wallet_service, broker_service, all_active_pairs
            )
        except Exception as e:
            logger.error(f"Error fetching price: {e}")

        await asyncio.sleep(settings.app_fetch_price_sleep)
