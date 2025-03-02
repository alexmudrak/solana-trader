from enum import Enum

MARKET_FEE = 1.001  # 0.1%


class Token(Enum):
    SOL = "So11111111111111111111111111111111111111112"
    USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


# TODO: Move to token Database table
class TokenDecimals(Enum):
    SOL = 1_000_000_000  # 1 SOL
    USDC = 1_000_000  # 1 USDC
