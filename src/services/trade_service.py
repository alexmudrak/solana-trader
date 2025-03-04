from datetime import UTC, datetime, timedelta
from itertools import groupby

from loguru import logger

from core.constants import MARKET_FEE
from models.orders_models import OrderBuy
from models.pair_models import TradingPairSettings
from models.prices_models import Price
from models.token_models import Token
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.prices_repository import PricesRepository
from schemas.trade_service_schemas import PriceByMinute
from services.transaction_service import TransactionService
from utils.trade_indicators import TradeIndicators


class TradeService:
    def __init__(
        self,
        transaction_service: TransactionService,
        trade_indicators: TradeIndicators,
        pair_settings: TradingPairSettings,
        prices_repository: PricesRepository,
        order_buy_repository: OrderBuyRepository,
        order_sell_repository: OrderSellRepository,
    ):
        self.transaction_service = transaction_service
        self.trade_indicators = trade_indicators
        self.prices = prices_repository
        self.order_buy = order_buy_repository
        self.order_sell = order_sell_repository
        self.base_token = pair_settings.from_token
        self.target_token = pair_settings.to_token
        # TODO: Need to remove in the production and
        #       get fee from FetcherService
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
        self.auto_buy_enabled = (
            self.trading_setting.auto_buy_enabled
        )  # Default False
        self.auto_sell_enabled = (
            self.trading_setting.auto_sell_enabled
        )  # Default False

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
            if self.auto_buy_enabled:
                await self.check_buy_order(
                    self.base_token,
                    self.target_token,
                    opened_orders,
                    last_price,
                )
        elif ema_short < ema_long and rsi_value > self.rsi_sell_threshold:
            if self.auto_sell_enabled:
                await self.check_sell_orders(
                    self.target_token,
                    self.base_token,
                    opened_orders,
                    last_price,
                )
        else:
            logger.log("ANALYZER", "🛑 No trading action taken.")

    async def check_sell_orders(
        self,
        from_token: Token,
        to_token: Token,
        opened_orders: list[OrderBuy],
        last_price,
    ):
        logger.log(
            "SELL", f"Found {len(opened_orders)} open orders for selling."
        )

        for order in opened_orders:
            sell_price_with_fee = last_price / MARKET_FEE
            order_amount = order.to_token_amount / order.to_token.decimals
            order_buy_price = order.price * order_amount
            order_sell_price = sell_price_with_fee * order_amount

            stop_loss_price = order_buy_price * (1 - self.stop_loss_percentage)
            take_profit_price = order_buy_price * (
                1 + self.take_profit_percentage
            )
            required_token_amount = order.to_token_amount

            if order_sell_price < stop_loss_price:
                logger.log(
                    "SELL",
                    f"{stop_loss_price:.2f} Sell order for order ID "
                    f"{order.id} triggered by stop loss.",
                )
                transaction_result = await self.transaction_service.sell(
                    from_token=from_token,
                    to_token=to_token,
                    sell_token_amount=required_token_amount,
                    last_market_price=last_price,
                )
                if not transaction_result:
                    message = f"Transaction failed: unable to complete the sell order id: {order.id}"
                    logger.critical(message)
                    return

                await self.order_sell.create(
                    from_token_id=from_token.id,
                    to_token_id=to_token.id,
                    from_token_amount=transaction_result.send_amount,
                    to_token_amount=transaction_result.receive_amount,
                    price=transaction_result.price,
                    buy_order_id=order.id,
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
                transaction_result = await self.transaction_service.sell(
                    from_token=from_token,
                    to_token=to_token,
                    sell_token_amount=required_token_amount,
                    last_market_price=last_price,
                    take_profit_price=take_profit_price,
                )
                if not transaction_result:
                    message = f"Transaction failed: unable to complete the sell order id: {order.id}"
                    logger.critical(message)
                    return

                await self.order_sell.create(
                    from_token_id=from_token.id,
                    to_token_id=to_token.id,
                    from_token_amount=transaction_result.send_amount,
                    to_token_amount=transaction_result.receive_amount,
                    price=transaction_result.price,
                    buy_order_id=order.id,
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
        last_price,
    ):
        total_open_orders = len(opened_orders)
        if total_open_orders >= self.buy_max_orders_threshold:
            log_message = (
                "Cannot create buy order: reached maximum "
                f"orders threshold ({self.buy_max_orders_threshold}). "
                f"Total orders: {total_open_orders}"
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

        transaction_result = await self.transaction_service.buy(
            from_token=from_token,
            to_token=to_token,
            buy_amount=self.buy_amount,
            last_market_price=last_price,
        )

        if not transaction_result:
            message = "Transaction failed: unable to complete the buy order."
            logger.critical(message)
            return

        await self.order_buy.create(
            from_token_id=from_token.id,
            to_token_id=to_token.id,
            from_token_amount=transaction_result.send_amount,
            to_token_amount=transaction_result.receive_amount,
            price=transaction_result.price,
        )

        log_message = (
            f"Buy order created for {self.buy_amount} "
            f"({transaction_result.price * self.buy_amount:.2f}) "
            f"{to_token.name} at price {transaction_result.price:.2f}. "
            f"Token count: {transaction_result.receive_amount}"
        )
        logger.log(
            "BUY",
            log_message,
        )
        logger.log(
            "NOTIF",
            log_message,
        )
