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

    # Fetcher settings
    app_fetch_price_sleep: int = 5

    # Database config
    app_db_url: str = "sqlite+aiosqlite:///solana_trade.db"
    app_telegram_bot: str | None = None
    app_telegram_admin: str | None = None

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
