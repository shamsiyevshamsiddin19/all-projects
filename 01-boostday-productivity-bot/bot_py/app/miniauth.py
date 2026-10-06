"""Telegram Mini App autentifikatsiyasi (WebApp initData HMAC tekshiruvi).

Mini app har so'rovda `Telegram.WebApp.initData` (imzolangan qator) yuboradi. Bu modul
uni bot tokeni bilan tekshiradi va foydalanuvchini serverda aniqlaydi — client soxta
`owner_id` yubora olmaydi. initData bo'lmasa (sayt backend'idan kelgan so'rov) — egaga (admin) biriktiriladi.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

from . import db
from .config import settings
from .helpers import user_get_or_create

logger = logging.getLogger("boostday")

# initData eskirgan deb hisoblanadigan maksimal yosh (24 soat).
MAX_AUTH_AGE = 24 * 60 * 60


def validate_init_data(init_data: str) -> dict | None:
    """initData'ni bot tokeni bilan tekshiradi. To'g'ri bo'lsa {'parsed', 'user'} qaytaradi, aks holda None."""
    if not init_data or not settings.BOT_TOKEN:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:  # noqa: BLE001
        return None

    received_hash = parsed.pop("hash", "")
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed.keys()))
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        return None

    # Yangiligini tekshiramiz (replay himoyasi).
    try:
        auth_date = int(parsed.get("auth_date", "0") or 0)
    except ValueError:
        auth_date = 0
    if auth_date and (time.time() - auth_date) > MAX_AUTH_AGE:
        return None

    user = None
    if parsed.get("user"):
        try:
            user = json.loads(parsed["user"])
        except (ValueError, TypeError):
            user = None

    return {"parsed": parsed, "user": user}


def resolve_owner(init_data: str, site_secret: str = "") -> dict:
    """So'rov egasini aniqlaydi.

    Qaytaradi: {"owner_id": int, "chat_id": int, "authenticated": bool, "ok": bool, "error": str}
      - initData bor va TO'G'RI  -> o'sha foydalanuvchi (kerak bo'lsa yaratiladi)
      - initData bor lekin NOTO'G'RI -> ok=False (rad etiladi)
      - initData YO'Q + to'g'ri SITE_SECRET -> admin (sayt orqali)
      - initData YO'Q + kalit yo'q/xato    -> ok=False (RAD ETILADI)

    MUHIM: ilgari initData'siz murojaat shartsiz admin sifatida qabul qilinardi —
    ya'ni `/boost/api?action=list` ni internetdagi har kim chaqira olardi. Endi
    sayt tomoni maxfiy kalit bilan tasdiqlanadi.
    """
    if init_data:
        info = validate_init_data(init_data)
        if not info or not info.get("user") or not info["user"].get("id"):
            return {"owner_id": 0, "chat_id": 0, "authenticated": False, "ok": False,
                    "error": "Telegram autentifikatsiyasi noto'g'ri"}
        try:
            user = user_get_or_create(info["user"])
        except Exception:  # noqa: BLE001
            logger.exception("Mini app user yaratishда xato")
            return {"owner_id": 0, "chat_id": 0, "authenticated": False, "ok": False, "error": "Foydalanuvchi xatosi"}
        return {"owner_id": int(user["id"]), "chat_id": int(user["chat_id"]), "authenticated": True,
                "ok": True, "error": ""}

    # initData yo'q -> faqat sayt maxfiy kaliti bilan
    if not settings.SITE_SECRET or not site_secret or \
            not hmac.compare_digest(str(site_secret), str(settings.SITE_SECRET)):
        return {"owner_id": 0, "chat_id": 0, "authenticated": False, "ok": False,
                "error": "Avtorizatsiya kerak"}

    if not settings.ADMIN_IDS:
        return {"owner_id": 0, "chat_id": 0, "authenticated": False, "ok": False, "error": "Egа topilmadi"}
    admin_chat_id = int(settings.ADMIN_IDS[0])
    row = db.one("SELECT id FROM users WHERE chat_id = :c", {"c": admin_chat_id})
    if not row:
        return {"owner_id": 0, "chat_id": 0, "authenticated": False, "ok": False,
                "error": "Egа topilmadi (admin botga /start bosishi kerak)"}
    return {"owner_id": int(row["id"]), "chat_id": admin_chat_id, "authenticated": False, "ok": True, "error": ""}
