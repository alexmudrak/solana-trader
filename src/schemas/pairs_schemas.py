from pydantic import BaseModel

from schemas.tokens_schemas import TokenResponse


class CreatePairsRequest(BaseModel):
    from_token_id: int
    to_token_id: int
    data_fetch_frequency: float
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

    class Config:
        from_attributes = True


class CreatePairsSettingsRequest(BaseModel):
    name: str
