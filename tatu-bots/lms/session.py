"""Foydalanuvchi LMS sessiyalarini keshlash (login'ni qayta-qayta qilmaslik uchun)."""
from __future__ import annotations

import time

from core import db
from .client import LmsClient, LoginError

# tg_id -> (client, last_used_ts)
_cache: dict[int, tuple[LmsClient, float]] = {}
TTL = 15 * 60  # 15 daqiqa


class NotRegistered(Exception):
    pass


async def get_session(tg_id: int) -> LmsClient:
    """Tizimga kirgan LmsClient qaytaradi (keshdan yoki yangi login)."""
    now = time.time()
    cached = _cache.get(tg_id)
    if cached and now - cached[1] < TTL:
        _cache[tg_id] = (cached[0], now)
        return cached[0]

    creds = await db.get_credentials(tg_id)
    if not creds:
        raise NotRegistered("Avval tizimga kiring: /login")

    # eski mijozni yopamiz
    if cached:
        try:
            await cached[0].close()
        except Exception:  # noqa: BLE001
            pass

    client = LmsClient()
    # foydalanuvchi Sozlamalarda tanlagan semestrni mijozga bog'laymiz
    u = await db.get_user(tg_id)
    if u and u.get("semester_id"):
        client.semester_id = int(u["semester_id"])
    try:
        await client.login(*creds)
    except Exception:
        await client.close()
        raise
    _cache[tg_id] = (client, now)
    return client


async def drop(tg_id: int) -> None:
    cached = _cache.pop(tg_id, None)
    if cached:
        try:
            await cached[0].close()
        except Exception:  # noqa: BLE001
            pass


async def cleanup_idle() -> None:
    now = time.time()
    for tid in [t for t, (_, ts) in _cache.items() if now - ts > TTL]:
        await drop(tid)


async def verify_login(login: str, password: str) -> str:
    """Login/parolni tekshirib, talaba ismini qaytaradi (ro'yxatdan o'tishda)."""
    client = LmsClient()
    try:
        await client.login(login, password)
        prof = await client.profile()
        return prof.full_name or ""
    finally:
        await client.close()
