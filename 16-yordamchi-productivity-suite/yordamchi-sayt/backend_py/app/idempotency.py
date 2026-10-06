"""Bir amalni IKKI MARTA bajarmaslik.

MUAMMO
======
Mijoz so'rov yuboradi → server uni BAJARADI → javob yo'lda yo'qoladi
(tarmoq uzildi, timeout, telefon uxlab qoldi). Mijoz uchun bu
"muvaffaqiyatsiz" ko'rinadi va u qayta yuboradi. Natijada lug'at
kategoriyasi, mashq yoki test bazasi IKKI MARTA saqlanadi.

Bu faqat nazariy emas: oflayn navbat (`core.js`) aynan shunday qayta
yuboradi, va uzilgan tarmoqda javob yo'qolishi odatiy hol.

YECHIM
======
Mijoz har YOZUV amaliga barqaror `X-Idempotency-Key` beradi (qayta
urinishlarda o'zgarmaydi). Birinchi marta biz kalitni band qilamiz, amalni
bajaramiz va javobni saqlaymiz. Takror kelganda amal QAYTA BAJARILMAYDI —
saqlangan javob aynan qaytariladi.

NOZIK JOYLAR
============
- Kalit `owner_key` bilan birga tekshiriladi: bir foydalanuvchining kaliti
  boshqasining javobini ocha olmaydi.
- Amal XATO bersa kalit o'chiriladi — aks holda vaqtinchalik 500 abadiy
  "saqlangan xato" bo'lib qolardi va qayta urinish hech qachon o'tmasdi.
- Yozuv boshlangan, lekin javob yozilmagan holat ("band") bo'lishi mumkin:
  ikkita so'rov bir vaqtda kelgan. Ikkinchisiga 409 beramiz — mijoz uni
  doimiy xato deb navbatdan chiqaradi, chunki birinchisi ishni tugatadi.
  Agar jarayon o'sha payt qulab tushgan bo'lsa, kalit `STALE_SECONDS` dan
  keyin bo'shatiladi, aks holda u abadiy tiqilib qolardi.
"""

from __future__ import annotations

import json
import logging
import random

from fastapi import Request
from starlette.responses import JSONResponse, Response

from . import db
from .errors import ApiError

logger = logging.getLogger("yordamchi")

HEADER = "X-Idempotency-Key"
MAX_KEY_LEN = 128
STALE_SECONDS = 120        # tugallanmagan yozuvni shundan keyin egallash mumkin
KEEP_HOURS = 24            # saqlangan javoblar shundan keyin keraksiz
CLEANUP_CHANCE = 0.02      # ~50 so'rovda bir marta tozalash


def key_from(request: Request) -> str:
    raw = (request.headers.get(HEADER) or "").strip()
    if raw == "" or len(raw) > MAX_KEY_LEN:
        return ""
    return raw


def begin(key: str, owner_key: str, action: str) -> Response | None:
    """Kalitni band qiladi.

    `None` — kalit BIZNIKI, amalni bajaring va `finish()` chaqiring.
    `Response` — takror so'rov, saqlangan javobni qaytaring.
    `ApiError(409)` — o'sha kalit hozir boshqa so'rovda bajarilmoqda.
    """
    # `execute_returning` — `fetch_one` EMAS: u commit qilmaydi va insert
    # jimgina yo'qolardi (2026-09-08 da test shuni topdi).
    inserted = db.execute_returning(
        "INSERT INTO idempotency_keys (key, owner_key, action) "
        "VALUES (:k, :o, :a) ON CONFLICT (key) DO NOTHING RETURNING key",
        {"k": key, "o": owner_key, "a": action[:64]},
    )
    if inserted is not None:
        if random.random() < CLEANUP_CHANCE:
            cleanup()
        return None

    row = db.fetch_one(
        "SELECT owner_key, status_code, response_body, "
        "       EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) AS age "
        "FROM idempotency_keys WHERE key = :k",
        {"k": key},
    )
    if row is None:                       # oradagi lahzada tozalab yuborilgan
        return None

    if str(row.get("owner_key") or "") != owner_key:
        # Boshqa odamning kaliti. Javobini KO'RSATMAYMIZ.
        raise ApiError("Bu so'rov kaliti boshqa foydalanuvchiga tegishli.", 409)

    if row.get("response_body") is not None:
        return Response(
            content=str(row["response_body"]),
            status_code=int(row.get("status_code") or 200),
            media_type="application/json",
        )

    # Javob hali yozilmagan.
    age = float(row.get("age") or 0)
    if age > STALE_SECONDS:
        # Oldingi urinish tugamagan (jarayon qulagan) — kalitni qayta egallaymiz.
        db.execute(
            "UPDATE idempotency_keys SET created_at = CURRENT_TIMESTAMP WHERE key = :k",
            {"k": key},
        )
        return None

    raise ApiError("Bu so'rov allaqachon bajarilmoqda.", 409)


def finish(key: str, response) -> None:
    """Javobni saqlaydi, keyingi takror shuni oladi."""
    body, status = _extract(response)
    if body is None:
        # Javobni matnga aylantirib bo'lmadi (masalan fayl oqimi) — kalitni
        # ushlab turishning ma'nosi yo'q, bo'shatamiz.
        release(key)
        return
    try:
        db.execute(
            "UPDATE idempotency_keys SET status_code = :s, response_body = :b WHERE key = :k",
            {"s": status, "b": body, "k": key},
        )
    except Exception:  # noqa: BLE001
        logger.exception("Idempotency javobini saqlab bo'lmadi (key=%s)", key)


def release(key: str) -> None:
    """Kalitni bo'shatadi — amal xato bergan holat uchun."""
    try:
        db.execute("DELETE FROM idempotency_keys WHERE key = :k", {"k": key})
    except Exception:  # noqa: BLE001
        logger.exception("Idempotency kalitini o'chirib bo'lmadi (key=%s)", key)


def cleanup() -> None:
    try:
        db.execute(
            "DELETE FROM idempotency_keys "
            "WHERE created_at < CURRENT_TIMESTAMP - (:h * INTERVAL '1 hour')",
            {"h": KEEP_HOURS},
        )
    except Exception:  # noqa: BLE001
        logger.exception("Idempotency tozalash xatosi")


def _extract(response) -> tuple[str | None, int]:
    status = int(getattr(response, "status_code", 200) or 200)
    if isinstance(response, (JSONResponse, Response)):
        raw = getattr(response, "body", None)
        if isinstance(raw, (bytes, bytearray)):
            try:
                return raw.decode("utf-8"), status
            except Exception:  # noqa: BLE001
                return None, status
    if isinstance(response, dict):
        try:
            return json.dumps(response, ensure_ascii=False), status
        except Exception:  # noqa: BLE001
            return None, status
    return None, status
