"""Mini app'dan galereya orqali tanlangan faylni Telegram'ga yuklab, `file_id` oladi.

Fayl foydalanuvchining bot bilan shaxsiy chatiga yuboriladi (bot allaqachon shu chat bilan
ulanishga ruxsatga ega — mini app faqat botni oldin ishga tushirgan foydalanuvchi uchun ochiladi),
so'ng olingan `file_id` qaytariladi va staging xabar darhol o'chiriladi (file_id o'zgarmay qoladi).
"""

from __future__ import annotations

import logging

from .tg import telegram, telegram_upload

logger = logging.getLogger("boostday")

MAX_UPLOAD_BYTES = 45 * 1024 * 1024  # ~45MB (Telegram bot API amaliy chegarasidan xavfsiz past)

_METHOD_FIELD = {
    "photo": ("sendPhoto", "photo"),
    "video": ("sendVideo", "video"),
    "audio": ("sendAudio", "audio"),
    "document": ("sendDocument", "document"),
}


def _extract_file_id(result: dict, field: str) -> str | None:
    node = result.get(field)
    if field == "photo" and isinstance(node, list) and node:
        return node[-1].get("file_id")
    if isinstance(node, dict):
        return node.get("file_id")
    return None


def upload_to_telegram(chat_id: int, kind: str, filename: str, content: bytes, content_type: str) -> dict:
    """Faylni yuklaydi. Muvaffaqiyatli bo'lsa {"ok": True, "file_id": str, "type": str}.

    `kind` mos kelmasa (masalan format sendPhoto/sendVideo qabul qilmasa) `document`
    sifatida avtomatik qayta uriniladi — deyarli har qanday fayl document sifatida o'tadi.
    """
    tried = [kind] if kind in _METHOD_FIELD else []
    if "document" not in tried:
        tried.append("document")

    last_error = "Fayl yuklanmadi"
    for attempt_kind in tried:
        method, field = _METHOD_FIELD[attempt_kind]
        files = {field: (filename or "file", content, content_type or "application/octet-stream")}
        data = {"chat_id": chat_id, "disable_notification": "true"}
        resp = telegram_upload(method, files, data)
        if resp and resp.get("ok"):
            result = resp.get("result") or {}
            file_id = _extract_file_id(result, field)
            message_id = result.get("message_id")
            if file_id:
                if message_id:
                    telegram("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                return {"ok": True, "file_id": file_id, "type": attempt_kind}
        if resp:
            last_error = str(resp.get("description") or "Telegram xatosi")
        else:
            last_error = "Telegramga ulanib bo'lmadi"
    return {"ok": False, "error": last_error}
