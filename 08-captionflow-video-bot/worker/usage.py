"""AI provayder API chaqiruvlarini hisoblash (Gemini / OpenAI).

Har bir chaqiruv Redis'da kunlik + oylik hisoblagichni oshiradi. Admin panel
(API & Limitlar) shu hisoblagichlardan sarflangan/qolgan limitni ko'rsatadi.

Eslatma: bitta video tarjimasi BIR NECHTA API chaqiruvi qiladi (oynalar +
tuzatish), shuning uchun videolar soni emas, aynan chaqiruvlar sanaladi.
Kunlik kalit Gemini'ning RPD (requests-per-day) limiti uchun muhim.
"""
from __future__ import annotations

import datetime as dt
import logging

from config import settings

logger = logging.getLogger(__name__)

_DAY_TTL = 3 * 24 * 3600      # kunlik kalit 3 kun saqlanadi
_MON_TTL = 40 * 24 * 3600     # oylik kalit 40 kun saqlanadi
_redis = None


def _client():
    global _redis
    if _redis is None:
        import redis  # celery broker uchun allaqachon o'rnatilgan
        _redis = redis.from_url(settings.celery_broker, socket_timeout=2)
    return _redis


def _keys(provider: str, now: dt.datetime) -> tuple[str, str]:
    return (f"api:{provider}:day:{now:%Y%m%d}", f"api:{provider}:mon:{now:%Y%m}")


def bump(provider: str, n: int = 1) -> None:
    """Provayder chaqiruvini +n qiladi (kunlik va oylik). Xato bo'lsa jim o'tadi."""
    try:
        c = _client()
        dk, mk = _keys(provider, dt.datetime.utcnow())
        pipe = c.pipeline()
        pipe.incrby(dk, n)
        pipe.expire(dk, _DAY_TTL)
        pipe.incrby(mk, n)
        pipe.expire(mk, _MON_TTL)
        pipe.execute()
    except Exception as e:  # hisoblagich asosiy oqimga xalal bermasin
        logger.debug("usage.bump(%s) xato: %s", provider, e)


def read(provider: str) -> tuple[int, int]:
    """(bugun, shu_oy) chaqiruvlar sonini qaytaradi."""
    try:
        c = _client()
        dk, mk = _keys(provider, dt.datetime.utcnow())
        vals = c.mget(dk, mk)
        return int(vals[0] or 0), int(vals[1] or 0)
    except Exception:
        return 0, 0
