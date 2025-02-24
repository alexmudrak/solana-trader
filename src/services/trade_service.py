from datetime import UTC, datetime, timedelta

from core.exceptions import (
    BuyAnalyserException,
    BuyPriceTooHigh,
    MarketFalling,
    MaximumOrdersReached,
    NotEnoughPrices,
)
from models.pair_models import TradingPairSettings
from models.prices_models import Price
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.prices_repository import PricesRepository


class TradeService:
    def __init__(
        self,
        pair_settings: TradingPairSettings,
        prices_repository: PricesRepository,
        order_buy_repository: OrderBuyRepository,
        order_sell_repository: OrderSellRepository,
    ):
        self.prices = prices_repository
        self.order_buy = order_buy_repository
        self.order_sell = order_sell_repository
        self.base_token = pair_settings.from_token
        self.target_token = pair_settings.to_token
        # TODO: Need to remove in the production and
        #       get fee from FetcherService
        self.market_fee = 1.0003  # 0.03%
        self.sell_threshold = 1
        self.buy_analysis_prices_count = 10
        self.buy_recent_prices_time_threshold = 60  # in minutes
        self.buy_recent_orders_time_threshold = 5  # in minutes
        self.buy_amount = 0.1
        self.buy_threshold = 0.5
        self.buy_max_orders_in_threshlod = 2

    async def is_sell_order_possible(
        self,
        sell_price: float,
        buy_price: float,
    ) -> bool:
        # This is simple algorithm to check
        # if will get profit from selling order
        return sell_price >= (buy_price + self.sell_threshold)

    async def is_buy_order_possible(
        self,
        current_price: float,
        recent_prices: list[Price],
        recent_orders_count: int,
    ) -> bool:
        if (
            not recent_prices
            or len(recent_prices) < self.buy_analysis_prices_count
        ):
            print("Not enough prices available for analysis.")
            raise NotEnoughPrices

        average_price = sum(price.price for price in recent_prices) / len(
            recent_prices
        )
        print(
            "[BUY] "
            f"Analyse last orders count: {len(recent_prices)} "
            f"Average: {average_price:.2f} "
            f"Current WITH FEE: {current_price:.2f} "
            f"Required: {average_price - self.buy_threshold:.2f}"
        )

        percentage_change = (
            (current_price - average_price) / average_price
        ) * 100
        print(f"[BUY] Percentage change: {percentage_change:.2f}%")
        if percentage_change < -5:
            print(
                f"[BUY] The market is falling: current buy price {current_price:.2f}, "
                f"average price {average_price:.2f}. Stopping purchases."
            )
            raise MarketFalling

        print(
            f"[BUY] Number of recent orders in the last {self.buy_recent_orders_time_threshold} minutes: {recent_orders_count}"
        )

        if recent_orders_count >= self.buy_max_orders_in_threshlod:
            print(
                f"[BUY] Maximum number of allowed orders ({self.buy_max_orders_in_threshlod}) reached. Stopping purchases."
            )
            raise MaximumOrdersReached

        if current_price > (average_price - self.buy_threshold):
            raise BuyPriceTooHigh

        return True

    async def check_sell_orders(self):
        last_price = await self.prices.get_latest(self.target_token.id)
        print(
            f"[SELL] Latest price WITHOUT FEE for {self.target_token.name}: {last_price:.2f}"
        )
        orders = await self.order_buy.get_opened_orders()
        print(f"[SELL] Found {len(orders)} open orders for selling.")

        for order in orders:
            # TODO: Implement getting fee from DEX market
            sell_price_with_fee = last_price / self.market_fee
            order_sell_price = sell_price_with_fee * order.amount

            if await self.is_sell_order_possible(
                order_sell_price,
                order.price,
            ):
                # TODO: Implement create order on DEX
                await self.order_sell.create(
                    order.to_token,
                    order.from_token,
                    order.amount,
                    order_sell_price,
                    order.id,
                )
                print(
                    f"[SELL] Sell order created for order ID {order.id} at price {order_sell_price:.2f}"
                )

    async def check_buy_order(self):
        last_price = await self.prices.get_latest(self.target_token.id)
        # TODO: Implement getting fee from DEX market
        buy_price_with_fee = last_price * self.market_fee
        recent_prices_time_threshold = datetime.now(UTC) - timedelta(
            minutes=self.buy_recent_prices_time_threshold
        )
        recent_orders_time_threshold = datetime.now(UTC) - timedelta(
            minutes=self.buy_recent_orders_time_threshold
        )

        recent_prices = await self.prices.get_recent_prices(
            self.target_token.id,
            recent_prices_time_threshold,
            descending=True,
        )
        recent_orders_count = await self.order_buy.get_recent_orders_count(
            self.target_token.id,
            recent_orders_time_threshold,
        )

        try:
            reason = None
            is_allow = await self.is_buy_order_possible(
                buy_price_with_fee,
                recent_prices,
                recent_orders_count,
            )
        except BuyAnalyserException as e:
            is_allow = False
            reason = e

        if is_allow:
            # TODO: Implement create order on DEX
            buy_price = self.buy_amount * buy_price_with_fee
            await self.order_buy.create(
                self.base_token.id,
                self.target_token.id,
                self.buy_amount,
                buy_price,
            )
            print(
                f"[BUY] Buy order created for {self.buy_amount} {self.target_token.name} at price {buy_price:.2f}."
            )
        else:
            print(
                f"[BUY] Conditions not met for buying {self.target_token.name} at price {buy_price_with_fee:.2f}. Reason: {reason}"
            )
