from datetime import UTC, datetime, timedelta

from core.constants import Token
from core.settings import settings
from models.prices_models import Price
from repositories.orders_buy_repository import OrderBuyRepository
from repositories.orders_sell_repository import OrderSellRepository
from repositories.prices_repository import PricesRepository


class TradeService:
    def __init__(
        self,
        prices_repository: PricesRepository,
        order_buy_repository: OrderBuyRepository,
        order_sell_repository: OrderSellRepository,
    ):
        self.prices = prices_repository
        self.order_buy = order_buy_repository
        self.order_sell = order_sell_repository
        self.token_name = Token.SOL.name
        self.utc_time_threshold = datetime.now(UTC) - timedelta(
            minutes=settings.app_time_threshold
        )
        # TODO: Need to remove in the production and
        #       get fee from FetcherService
        self.market_fee = 1.0003  # 0.03%
        self.sell_threshold = 1
        self.analysis_prices_count = 10
        self.buy_amount = 0.3
        self.buy_threshold = 0.5
        self.buy_from_token_name = Token.USDC.name

    async def __can_sell_order(
        self,
        sell_price: float,
        buy_price: float,
    ) -> bool:
        # This is simple algorithm to check
        # if will get profit from selling order
        return (sell_price - buy_price) > self.sell_threshold

    async def __can_buy_order(
        self, current_price: float, recent_prices: list[Price]
    ) -> bool:
        if (
            not recent_prices
            or len(recent_prices) < self.analysis_prices_count
        ):
            print("Not enough prices available for analysis.")
            return False

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

        if percentage_change < -5:
            print(
                f"The market is falling: current buy price {current_price:.2f}, "
                f"average price {average_price:.2f}. Stopping purchases."
            )
            return False

        return current_price < (average_price - self.buy_threshold)

    async def check_sell_orders(self):
        last_price = await self.prices.get_latest(self.token_name)
        print(
            f"[SELL] Latest price WITHOUT FEE for {self.token_name}: {last_price:.2f}"
        )
        orders = await self.order_buy.get_opened_orders()
        print(f"[SELL] Found {len(orders)} open orders for selling.")

        for order in orders:
            # TODO: Implement getting fee from DEX market
            sell_price_with_fee = last_price / self.market_fee
            order_sell_price = sell_price_with_fee * order.amount

            if await self.__can_sell_order(
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
        last_price = await self.prices.get_latest(self.token_name)
        # TODO: Implement getting fee from DEX market
        buy_price_with_fee = last_price * self.market_fee

        recent_prices = await self.prices.get_recent_prices(
            self.token_name,
            self.utc_time_threshold,
        )

        if await self.__can_buy_order(
            buy_price_with_fee,
            recent_prices,
        ):
            # TODO: Implement create order on DEX
            buy_price = self.buy_amount * buy_price_with_fee
            await self.order_buy.create(
                self.buy_from_token_name,
                self.token_name,
                self.buy_amount,
                buy_price,
            )
            print(
                f"[BUY] Buy order created for {self.buy_amount} {self.token_name} at price {buy_price:.2f}."
            )
        else:
            print(
                f"[BUY] Conditions not met for buying {self.token_name} at price {buy_price_with_fee:.2f}."
            )
