import asyncio
import sys

from loguru import logger

from brokers.abstract_market import AbstractMarket
from brokers.jupiter_market import JupiterMarket
from core.constants import MARKET_FEE, Token
from core.database import get_session
from core.settings import settings
from models.pair_models import TradingPairSettings
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.pairs_repository import PairsRepository
from repositories.prices_repository import PricesRepository
from services.trade_service import TradeService
from services.transaction_service import TransactionService
from services.wallet_service import WalletService
from utils.trade_indicators import TradeIndicators


async def get_latest_price(
    market_service: AbstractMarket,
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

        result = await market_service.get_price(
            from_token=from_token.value,
            to_tokens=to_tokens_list,
        )
        for pair_setting in pairs_settings:
            to_token = pair_setting.to_token
            price = float(result["data"][to_token.address]["price"])

            await prices_repository.create(price, to_token.id)

            # TODO: Implement getting fee from DEX market
            buy_price_with_fee = price * MARKET_FEE
            sell_price_with_fee = price / MARKET_FEE

            logger.opt(colors=True).log(
                "FETCHER",
                f"Current <red>WITHOUT FEE</red> price for <underline><b>{from_token.name}</b></underline> to <underline><b>{to_token.name}</b></underline>: <white>{price:.2f}</white>",
            )
            logger.opt(ansi=True).log(
                "FETCHER",
                f"<green>BUY</green> price with FEE: <white>{buy_price_with_fee:.2f}</white>",
            )
            logger.opt(colors=True).log(
                "FETCHER",
                f"<red>SELL</red> price with FEE: <white>{sell_price_with_fee:.2f}</white>",
            )


async def trade_execution(
    transaction_service: TransactionService,
    trade_indicators: TradeIndicators,
    pairs_settings: list[TradingPairSettings],
):
    for pair_settings in pairs_settings:
        async for session in get_session():
            prices_repository = PricesRepository(session)
            orders_buy_repository = OrderBuyRepository(session)
            orders_sell_repository = OrderSellRepository(session)

            trader = TradeService(
                transaction_service,
                trade_indicators,
                pair_settings,
                prices_repository,
                orders_buy_repository,
                orders_sell_repository,
            )
            await trader.analyzer()


async def run_background_processes():
    all_active_pairs = []
    market_service = JupiterMarket()
    wallet_service = WalletService()
    transaction_service = TransactionService(
        wallet_service,
        market_service,
    )
    trade_indicators = TradeIndicators()

    while True:
        try:
            async for session in get_session():
                pairs_repository = PairsRepository(session)
                all_active_pairs = await pairs_repository.get_pairs(
                    only_active=True
                )
                await get_latest_price(
                    market_service,
                    all_active_pairs,
                )
                await trade_execution(
                    transaction_service,
                    trade_indicators,
                    all_active_pairs,
                )
        except Exception as e:
            exception = sys.exc_info()
            logger.opt(exception=exception).error(
                f"Error fetching price: {e}", exec
            )

        await asyncio.sleep(settings.app_fetch_price_sleep)
