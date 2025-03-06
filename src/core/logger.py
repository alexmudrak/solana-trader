import sys

from loguru import logger

from core.settings import settings
from services.notification_service import notifier


def setup_logger():
    logger.remove()
    logger.opt(colors=True)
    logger.level("FETCHER", no=38, color="<light-black>")
    logger.level("ANALYZER", no=39, color="<light-white>")
    logger.level("SELL", no=40, color="<red>")
    logger.level("BUY", no=41, color="<green>")
    logger.level("INDICATOR", no=42, color="<light-yellow>")
    logger.level("NOTIF", no=999)

    logger.add(
        sys.stderr,
        level=settings.app_log_level,
        format="<light-black>{time:YYYY-MM-DD at HH:mm:ss}</light-black> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>",
        backtrace=True,
        diagnose=True,
    )

    logger.add(
        notifier.notify,
        level="NOTIF",
        filter={"apprise": False},
        format="{message}\n\n\n{time:YYYY-MM-DD at HH:mm:ss}",
    )
