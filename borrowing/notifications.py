import requests
from django.conf import settings

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID
URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_telegram_notification(message: str) -> None:
    requests.post(URL, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
