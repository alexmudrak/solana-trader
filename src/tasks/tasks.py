import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from brokers.jupiter_market import JupiterMarket
from core.constants import MAIN_TOKEN, Token
from core.database import get_session
from models.orders_models import OrderBuy, OrderSell
from models.prices_models import Price


async def get_prices_background(from_token: Token, to_token: Token):
    market = JupiterMarket()
    while True:
        try:
            session = await anext(get_session())
            result = await market.get_price(from_token.value, to_token.value)

            price = float(result["data"][from_token.value]["price"])

            async with session:
                new_price = Price(
                    token_name=from_token.name,
                    price=price,
                    created=datetime.now(UTC),
                )
                session.add(new_price)
                await session.commit()
            print(f"Current Price 1: {from_token} to {to_token} - {price}")
            await analyse_orders(price)
        except Exception as e:
            print(f"Error fetching price: {e}")
        await asyncio.sleep(5)


async def analyse_orders(
    new_price: float,
):
    token_name = "SOL"
    threshold_buy = 0.5
    threshold_sell = 1
    fee_price = 1.0003
    current_price = new_price
    sell_current_price = current_price / fee_price
    buy_current_price = current_price * fee_price
    buy_token_count = 0.3
    minimum_prices_count = 9

    minutes_ago = datetime.now(UTC) - timedelta(minutes=5)

    print(f"Original price: {current_price:.2f}")
    print(f"Sell price after fees: {sell_current_price:.2f}")
    print(f"Buy price with fees: {buy_current_price:.2f}")

    try:
        # Check to SELL orders
        session = await anext(get_session())
        async with session:
            query = await session.execute(
                select(OrderBuy)
                .outerjoin(OrderBuy.sells)
                .where(OrderBuy.sells.is_(None))
            )
            orders = query.scalars().all()
            if not orders:
                print("No buy orders found without sells.")

            for order in orders:
                buy_price = order.price / order.amount
                if (sell_current_price - buy_price) > threshold_sell:
                    order_sell = OrderSell(
                        from_token=order.to_token,
                        to_token=MAIN_TOKEN,
                        amount=order.amount,
                        price=order.amount * sell_current_price,
                        buy_order_id=order.id,
                    )
                    session.add(order_sell)
                    await session.commit()
                    print(f"Sell order created: {order_sell.id}")

        # Check to BUY order
        session = await anext(get_session())
        async with session:
            stmt = (
                select(Price)
                .where(
                    Price.token_name == token_name,
                    Price.created >= minutes_ago,
                )
                .order_by(Price.created.desc())
            )
            query = await session.execute(stmt)
            prices = query.scalars().all()

            if not prices or len(prices) < minimum_prices_count:
                print("Not enough prices available for analysis.")
                return

            average_price = sum(price.price for price in prices) / len(prices)
            print(
                f"Average price over the last {len(prices)} orders: {average_price:.2f}. Required: {average_price - threshold_buy:.2f}"
            )
            percentage_change = (
                (buy_current_price - average_price) / average_price
            ) * 100

            if percentage_change < -5:
                print(
                    f"The market is falling: current buy price {buy_current_price:.2f}, average price {average_price:.2f}. Stopping purchases."
                )
                return

            if buy_current_price < (average_price - threshold_buy):
                print(f"Buying {token_name} at price {buy_current_price:.2f}.")
                order = OrderBuy(
                    from_token=MAIN_TOKEN,
                    to_token=token_name,
                    amount=buy_token_count,
                    price=buy_token_count * buy_current_price,
                )
                session.add(order)
                await session.commit()
                print(f"Buy order created: {order.id}")
            else:
                print(f"Conditions not met for buying {token_name}.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
