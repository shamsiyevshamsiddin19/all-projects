import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def send_telegram_notification(text: str) -> bool:
    """
    Sends a Markdown-formatted or plain text notification to the admin Telegram chat.
    Fails silently with a logged warning so payment or web flows are never blocked.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "")

    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
            logger.warning(f"Telegram notification failed ({resp.status_code}): {resp.text}")
            return False
        return True
    except Exception as exc:
        logger.warning(f"Error sending Telegram notification: {exc}")
        return False
