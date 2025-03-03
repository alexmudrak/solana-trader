from datetime import UTC, datetime, timedelta
from itertools import groupby

from loguru import logger

from brokers.abstract_market import AbstractMarket
from core.constants import MARKET_FEE
from models.orders_models import OrderBuy
from models.pair_models import TradingPairSettings
from models.prices_models import Price
from models.token_models import Token
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.prices_repository import PricesRepository
from schemas.trade_service_schemas import PriceByMinute
from services.wallet_service import WalletService
from utils.trade_indicators import TradeIndicators


class TradeService:
    def __init__(
        self,
        wallet_service: WalletService,
        broker_service: AbstractMarket,
        trade_indicators: TradeIndicators,
        pair_settings: TradingPairSettings,
        prices_repository: PricesRepository,
        order_buy_repository: OrderBuyRepository,
        order_sell_repository: OrderSellRepository,
    ):
        self.wallet = wallet_service
        self.broker_service = broker_service
        self.trade_indicators = trade_indicators
        self.prices = prices_repository
        self.order_buy = order_buy_repository
        self.order_sell = order_sell_repository
        self.base_token = pair_settings.from_token
        self.target_token = pair_settings.to_token
        # TODO: Need to remove in the production and
        #       get fee from FetcherService
        self.market_fee = MARKET_FEE
        self.trading_setting = pair_settings.trading_setting
        self.take_profit_percentage = (
            self.trading_setting.take_profit_percentage
        )  # default 0.05 -> 5% profit
        self.stop_loss_percentage = (
            self.trading_setting.stop_loss_percentage
        )  # default 0.05 -> 5% loss
        self.short_ema_time_period = (
            self.trading_setting.short_ema_time_period
        )  # default 5, in minutes
        self.long_ema_time_period = (
            self.trading_setting.long_ema_time_period
        )  # default 20, in minutes
        self.rsi_buy_threshold = (
            self.trading_setting.rsi_buy_threshold
        )  # default 30
        self.rsi_sell_threshold = (
            self.trading_setting.rsi_sell_threshold
        )  # default 70
        self.rsi_time_period = (
            self.trading_setting.rsi_time_period
        )  # default 14, in minutes
        self.buy_amount = self.trading_setting.buy_amount  # default 0.1
        self.buy_max_orders_threshold = (
            self.trading_setting.buy_max_orders_threshold
        )  # default 2
        self.buy_max_orders_in_last_period = (
            self.trading_setting.buy_max_orders_in_last_period
        )  # default 1
        self.buy_check_period_minutes = (
            self.trading_setting.buy_check_period_minutes
        )  # default 60

    def get_prices_list_by_minutes(
        self, prices: list[Price]
    ) -> list[PriceByMinute]:
        minute_prices = []

        for _, group in groupby(
            prices, key=lambda p: p.created.strftime("%Y-%m-%d %H:%M")
        ):
            prices_list = list(group)
            avg_price = sum(price.price for price in prices_list) / len(
                prices_list
            )
            minute_prices.append(
                PriceByMinute(
                    time=prices_list[0].created,
                    value=avg_price,
                )
            )

        return minute_prices

    async def analyzer(self):
        last_price = await self.prices.get_latest(self.target_token.id)
        # TODO: Implement getting fee from DEX market
        buy_price_with_fee = last_price * self.market_fee
        sell_price_with_fee = last_price / self.market_fee

        logger.opt(ansi=True).log(
            "ANALYZER",
            f"<green>BUY</green> price with FEE: <white>{buy_price_with_fee:.2f}</white>",
        )
        logger.opt(colors=True).log(
            "ANALYZER",
            f"<red>SELL</red> price with FEE: <white>{sell_price_with_fee:.2f}</white>",
        )

        time_threshold = datetime.now(UTC) - timedelta(
            minutes=20,
        )
        prices = await self.prices.get_recent_prices(
            self.target_token.id,
            time_threshold,
        )

        price_list_by_minutes = self.get_prices_list_by_minutes(prices)

        ema_short = self.trade_indicators.calculate_ema(
            price_list_by_minutes, self.short_ema_time_period
        )
        ema_long = self.trade_indicators.calculate_ema(
            price_list_by_minutes, self.long_ema_time_period
        )
        rsi_value = self.trade_indicators.calculate_rsi(
            price_list_by_minutes, self.rsi_time_period
        )

        opened_orders = await self.order_buy.get_opened_orders()
        logger.opt(colors=True).log(
            "ANALYZER",
            f"Found <white>{len(opened_orders)}</white> open orders.",
        )

        if len(price_list_by_minutes) > 1:
            previous_price = price_list_by_minutes[-2].value
            current_price = price_list_by_minutes[-1].value
            if current_price > previous_price:
                logger.opt(colors=True).log(
                    "ANALYZER", "Market is trending <green>UP ⬆️</green>."
                )
            elif current_price < previous_price:
                logger.opt(colors=True).log(
                    "ANALYZER", "Market is trending <red>DOWN ⬇️</red>."
                )

        if ema_short > ema_long and rsi_value < self.rsi_buy_threshold:
            await self.check_buy_order(
                self.base_token,
                self.target_token,
                opened_orders,
                buy_price_with_fee,
            )
        elif ema_short < ema_long and rsi_value > self.rsi_sell_threshold:
            await self.check_sell_orders(
                self.target_token,
                self.base_token,
                opened_orders,
                sell_price_with_fee,
            )
        else:
            logger.log("ANALYZER", "🛑 No trading action taken.")

    async def check_sell_orders(
        self,
        from_token: Token,
        to_token: Token,
        opened_orders: list[OrderBuy],
        sell_price_with_fee: float,
    ):
        logger.log(
            "SELL", f"Found {len(opened_orders)} open orders for selling."
        )

        for order in opened_orders:
            order_amount = order.to_token_amount / order.to_token.decimals
            order_buy_price = order.price * order_amount
            order_sell_price = sell_price_with_fee * order_amount

            stop_loss_price = order_buy_price * (1 - self.stop_loss_percentage)
            take_profit_price = order_buy_price * (
                1 + self.take_profit_percentage
            )
            receive_token_amount = take_profit_price * to_token.decimals
            required_token_amount = order.to_token_amount

            if order_sell_price < stop_loss_price:
                logger.log(
                    "SELL",
                    f"{stop_loss_price:.2f} Sell order for order ID "
                    f"{order.id} triggered by stop loss.",
                )

                # Check wallet balance
                base_token_balance = await self.wallet.get_balance(to_token)
                if (
                    not base_token_balance.token
                    or required_token_amount > base_token_balance.amount
                ):
                    logger.warning(
                        "Insufficient balance for selling. "
                        f"Required: {required_token_amount}, "
                        f"Available: {base_token_balance.amount if base_token_balance.token else 0}"
                    )
                    return

                # Make swap transaction
                dex_quote = await self.broker_service.get_quote_tokens(
                    from_token.address,
                    to_token.address,
                    required_token_amount,
                )

                (
                    await self.broker_service.make_transaction(
                        dex_quote, str(self.wallet.pub_key)
                    )
                )
                dex_receive_amount = int(dex_quote["outAmount"])

                # Send transaction
                # TODO: Uncomment when all methods will tests
                # await self.wallet.send_transaction(dex_transaction_instructions)
                await self.order_sell.create(
                    from_token.id,
                    to_token.id,
                    required_token_amount,
                    dex_receive_amount,
                    sell_price_with_fee,
                    order.id,
                )
                log_message = (
                    f"Sell order created due to stop loss for order ID {order.id}. "
                    f"Buy price: {order_buy_price:.2f}, "
                    f"Sell price: {order_sell_price:.2f}, "
                    f"Stop loss price: {stop_loss_price:.2f}"
                )
                logger.log("SELL", log_message)
                logger.log(
                    "NOTIF",
                    log_message,
                )
            elif order_sell_price >= take_profit_price:
                # Make swap transaction
                dex_quote = await self.broker_service.get_quote_tokens(
                    from_token.address,
                    to_token.address,
                    required_token_amount,
                )

                (
                    await self.broker_service.make_transaction(
                        dex_quote, str(self.wallet.pub_key)
                    )
                )
                dex_receive_amount = int(dex_quote["outAmount"])
                dex_swap_value = float(dex_quote["swapUsdValue"])

                if dex_receive_amount < receive_token_amount:
                    logger.critical(
                        "Received amount from DEX is less than expected. "
                        f"Get: {dex_receive_amount} expect: {receive_token_amount}"
                    )
                    return

                if dex_swap_value < take_profit_price:
                    logger.critical("Get less than expected")
                    return

                # Check wallet balance
                base_token_balance = await self.wallet.get_balance(to_token)
                if (
                    not base_token_balance.token
                    or required_token_amount > base_token_balance.amount
                ):
                    logger.warning(
                        "Insufficient balance for selling. "
                        f"Required: {required_token_amount}, "
                        f"Available: {base_token_balance.amount if base_token_balance.token else 0}"
                    )
                    return

                # Send transaction
                # TODO: Uncomment when all methods will tests
                # await self.wallet.send_transaction(dex_transaction_instructions)
                await self.order_sell.create(
                    from_token.id,
                    to_token.id,
                    required_token_amount,
                    dex_receive_amount,
                    sell_price_with_fee,
                    order.id,
                )
                log_message = (
                    f"Sell order created for order ID {order.id}. "
                    f"Buy price: {order_buy_price:.2f}, "
                    f"Sell price: {order_sell_price:.2f}, "
                    f"Take profit: {order_sell_price - order_buy_price:.2f}. "
                    f"Price profit: {take_profit_price / order_amount:.2f}"
                )
                logger.log(
                    "SELL",
                    log_message,
                )
                logger.log(
                    "NOTIF",
                    log_message,
                )
            else:
                log_message = (
                    f"Order ID {order.id}: Not profitable to sell or stop-loss not triggered. "
                    f"Buy price: {order_buy_price:.2f}, "
                    f"Sell price: {order_sell_price:.2f}, "
                    f"Take profit: {order_sell_price - order_buy_price:.2f}. "
                    f"Price profit: {take_profit_price / order_amount:.2f}"
                )
                logger.log(
                    "SELL",
                    log_message,
                )

    async def check_buy_order(
        self,
        from_token: Token,
        to_token: Token,
        opened_orders: list[OrderBuy],
        buy_price_with_fee: float,
    ):
        total_open_orders = len(opened_orders)
        if total_open_orders > self.buy_max_orders_threshold:
            log_message = (
                "Cannot create buy order: reached maximum "
                f"orders threshold ({self.buy_max_orders_threshold})."
            )
            logger.log(
                "BUY",
                log_message,
            )
            return

        current_time = datetime.now(UTC)
        time_threshold = current_time - timedelta(
            minutes=self.buy_check_period_minutes
        )
        naive_time_threshold = time_threshold.replace(tzinfo=None)

        recent_orders = [
            order
            for order in opened_orders
            if order.created >= naive_time_threshold
        ]

        if len(recent_orders) >= self.buy_max_orders_in_last_period:
            logger.warning(
                "Cannot create buy order: reached maximum orders threshold "
                f"of {self.buy_max_orders_in_last_period} "
                f"within the last {self.buy_check_period_minutes} minutes. "
                f"Current recent orders: {len(recent_orders)}."
            )
            return

        receive_token_amount = int(to_token.decimals * self.buy_amount)
        required_token_amount = int(
            buy_price_with_fee * from_token.decimals * self.buy_amount
        )

        # Make swap transaction
        dex_quote = await self.broker_service.get_quote_tokens(
            from_token.address,
            to_token.address,
            required_token_amount,
        )
        dex_receive_amount = int(dex_quote["outAmount"])
        dex_swap_value = float(dex_quote["swapUsdValue"])

        if dex_receive_amount < receive_token_amount:
            logger.critical(
                "Received amount from DEX is less than expected. "
                f"Get: {dex_receive_amount} expect: {receive_token_amount}"
            )
            return

        if dex_swap_value > (buy_price_with_fee * self.buy_amount):
            logger.critical("Spend more than expected")
            return

        (
            await self.broker_service.make_transaction(
                dex_quote, str(self.wallet.pub_key)
            )
        )

        # Check wallet balance
        base_token_balance = await self.wallet.get_balance(from_token)
        if (
            not base_token_balance.token
            or required_token_amount > base_token_balance.token.amount
        ):
            logger.warning(
                "Insufficient balance for buying. "
                f"Required: {required_token_amount}, "
                f"Available: {base_token_balance.token.amount if base_token_balance.token else 0}"
            )
            return

        # Send transaction
        # TODO: Uncomment when all methods will tests
        # await self.wallet.send_transaction(dex_transaction_instructions)

        await self.order_buy.create(
            from_token.id,
            to_token.id,
            required_token_amount,
            receive_token_amount,
            buy_price_with_fee,
        )

        log_message = (
            f"Buy order created for {self.buy_amount} "
            f"({buy_price_with_fee * self.buy_amount:.2f}) "
            f"{to_token.name} at price {buy_price_with_fee:.2f}. "
            f"Token count: {required_token_amount}"
        )
        logger.log(
            "BUY",
            log_message,
        )
        logger.log(
            "NOTIF",
            log_message,
        )
