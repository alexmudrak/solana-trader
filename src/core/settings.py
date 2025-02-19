import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Logger setup
    app_log_level: str = "INFO"
    app_debug: bool = False
    logging.basicConfig(level=app_log_level)

    if app_log_level != "DEBUG":
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)

    # Database config
    app_db_url: str = "sqlite+aiosqlite:///solana_trade.db"

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
