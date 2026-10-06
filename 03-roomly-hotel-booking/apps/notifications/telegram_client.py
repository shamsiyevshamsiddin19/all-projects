"""Celery (sync) kontekstidan Telegram Bot API'ga to'g'ridan-to'g'ri HTTP orqali xabar yuborish.

aiogram Bot obyekti async bo'lgani uchun Celery task'lar ichida uni qayta ishga
tushirish o'rniga oddiy HTTP so'rov ishlatiladi — soddaroq va ishonchli.
"""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def send_message(chat_id, text: str, reply_markup: dict | None = None) -> bool:
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN sozlanmagan, xabar yuborilmadi: %s", text[:50])
        return False

    url = TELEGRAM_API_BASE.format(token=settings.BOT_TOKEN, method="sendMessage")
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Telegramga xabar yuborishda xatolik: chat_id=%s", chat_id)
        return False
