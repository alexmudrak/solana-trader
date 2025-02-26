from pydantic import BaseModel

from schemas.tokens_schemas import TokenResponse


class CreatePairsRequest(BaseModel):
    from_token_id: int
    to_token_id: int
    trading_setting_id: int


class PairsResponse(BaseModel):
    id: int
    from_token: TokenResponse
    to_token: TokenResponse
    trading_setting: "PairsSettingsResponse"

    class Config:
        from_attributes = True


class PairsSettingsResponse(BaseModel):
    id: int
    name: str
    take_profit_percentage: float
    stop_loss_percentage: float
    short_ema_time_period: int
    long_ema_time_period: int
    rsi_buy_threshold: int
    rsi_sell_threshold: int
    rsi_time_period: int
    buy_amount: float
    buy_max_orders_threshold: int

    class Config:
        from_attributes = True


class CreatePairsSettingsRequest(BaseModel):
    name: str


class UpdatePairSettingsRequest(BaseModel):
    buy_amount: float
    buy_max_orders_threshold: int
    long_ema_time_period: int
    rsi_buy_threshold: int
    rsi_sell_threshold: int
    rsi_time_period: int
    short_ema_time_period: int
    stop_loss_percentage: float
    take_profit_percentage: float
