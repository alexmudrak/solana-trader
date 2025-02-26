from schemas.trade_service_schemas import PriceByMinute


class TradeIndicators:
    @staticmethod
    def calculate_ema(prices: list[PriceByMinute], period: int) -> float:
        if len(prices) < period:
            raise ValueError("Not enough data for EMA")

        initial_ema = sum(price.value for price in prices[:period]) / period
        alpha = 2 / (period + 1)

        ema = initial_ema

        for price in prices[period:]:
            ema = (price.value - ema) * alpha + ema

        print(f"[INDICATOR] EMA (period {period}): {ema:.2f}")

        return ema

    @staticmethod
    def calculate_rsi(prices: list[PriceByMinute], period: int) -> float:
        if len(prices) < period:
            raise ValueError("Not enough data for RSI")

        gains = []
        losses = []

        for num in range(1, len(prices)):
            change = prices[num].value - prices[num - 1].value

            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)

        average_gain = sum(gains[:period]) / period
        average_loss = sum(losses[:period]) / period
        rsi_values = []

        for i in range(period, len(prices) - 1):
            gain = gains[i]
            loss = losses[i]

            average_gain = (average_gain * (period - 1) + gain) / period
            average_loss = (average_loss * (period - 1) + loss) / period

            if average_loss == 0:
                rsi = 100
            else:
                rs = average_gain / average_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

        print(
            f"[INDICATOR] RSI (period {period}): {rsi_values[-1]:.2f}. Avg gain: {average_gain * 100:.2f}, Avg losses: {average_loss * 100:.2f}"
        )

        return rsi_values[-1]
