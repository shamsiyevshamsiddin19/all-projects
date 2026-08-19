"""Web Push — telefondagi HAQIQIY bildirishnoma (Instagram/YouTube kabi).

Telegram xabaridan farqi: bildirishnoma qulflangan ekranda, tizim
bildirishnomalar panelida chiqadi va ilova ochiq bo'lishi shart emas.

Ishlash tartibi:
  1. Brauzer (service worker) `PushManager.subscribe()` bilan obuna bo'ladi
     va `endpoint` + shifrlash kalitlarini beradi -> `push_subs` jadvali.
  2. Server VAPID kaliti bilan imzolab, o'sha `endpoint`ga so'rov yuboradi
     (Chrome uchun bu FCM manzili).
  3. Service worker `push` hodisasini ushlab, bildirishnoma ko'rsatadi.

VAPID kalitlari `.env` da (`VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`).
Maxfiy kalit HECH QACHON brauzerga berilmaydi — faqat ochiq kalit.
"""

from __future__ import annotations

import json
import logging

from . import db
from .config import settings

logger = logging.getLogger("boostday")

# Obuna endi yaroqsiz — brauzer ruxsatni olib tashlagan yoki ilova o'chirilgan.
# Bunday obunani saqlab turishning ma'nosi yo'q, o'chiramiz.
_DEAD_CODES = (404, 410)


def enabled() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def subscriptions(owner_id: int = 0) -> list:
    if not db.table_exists("push_subs"):
        return []
    if owner_id > 0:
        return db.all_("SELECT id, endpoint, p256dh, auth FROM push_subs "
                       "WHERE is_active = 1 AND (owner_id = :u OR owner_id = 0)", {"u": owner_id})
    return db.all_("SELECT id, endpoint, p256dh, auth FROM push_subs WHERE is_active = 1")


def _deactivate(sub_id: int, reason: str) -> None:
    db.run("UPDATE push_subs SET is_active = 0 WHERE id = :id", {"id": sub_id})
    logger.info("PUSH obuna o'chirildi id=%s sabab=%s", sub_id, reason)


def send(owner_id: int, title: str, body: str = "", url: str = "/", tag: str = "") -> int:
    """Bildirishnoma yuboradi. Qaytaradi: nechta qurilmaga yetib bordi.

    Bitta qurilma yiqilsa qolganlari baribir yuboriladi — shuning uchun
    har biri alohida `try` ichida.
    """
    if not enabled():
        logger.warning("PUSH: VAPID kalitlari sozlanmagan — yuborilmadi")
        return 0

    subs = subscriptions(owner_id)
    if not subs:
        return 0

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.error("PUSH: pywebpush o'rnatilmagan")
        return 0

    payload = json.dumps({
        "title": title, "body": body, "url": url,
        "tag": tag or "yordamchi",
    }, ensure_ascii=False)

    sent = 0
    for s in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": s["endpoint"],
                    "keys": {"p256dh": s["p256dh"], "auth": s["auth"]},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT or "mailto:admin@example.com"},
                timeout=10,
            )
            db.run("UPDATE push_subs SET last_ok_at = CURRENT_TIMESTAMP WHERE id = :id",
                   {"id": int(s["id"])})
            sent += 1
        except WebPushException as exc:  # noqa: PERF203 — har biri mustaqil
            code = getattr(getattr(exc, "response", None), "status_code", 0)
            if code in _DEAD_CODES:
                _deactivate(int(s["id"]), f"HTTP {code}")
            else:
                logger.warning("PUSH yuborilmadi id=%s: %s", s["id"], exc)
        except Exception:  # noqa: BLE001
            logger.exception("PUSH kutilmagan xato id=%s", s["id"])
    return sent
