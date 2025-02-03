from pydantic_settings import BaseSettings


class AppSettigs(BaseSettings):
    app_wallet_file_name: str | None = "wallet_keypair.json"
    app_open_ai_api_key: str | None = None
    app_solana_keypair_json: str | None = None
    app_solana_rpc_url: str | None = None
    app_solana_websocket_url: str | None = None

    class Config:
        env_file = ".env"


settings = AppSettigs()
