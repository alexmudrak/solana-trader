class BuyAnalyserException(Exception):
    pass


class NotEnoughPrices(BuyAnalyserException):
    def __init__(self, message="Not enough prices available for analysis."):
        super().__init__(message)


class MarketFalling(BuyAnalyserException):
    def __init__(self, message="The market is falling."):
        super().__init__(message)


class MaximumOrdersReached(BuyAnalyserException):
    def __init__(self, message="Maximum number of allowed orders reached."):
        super().__init__(message)


class BuyPriceTooHigh(BuyAnalyserException):
    def __init__(self, message="The buy price is too high."):
        super().__init__(message)
