import apprise

from core.settings import settings

notifier = apprise.Apprise()
notifier.add(
    f"tgram://{settings.app_telegram_bot}/{settings.app_telegram_admin}/"
)
