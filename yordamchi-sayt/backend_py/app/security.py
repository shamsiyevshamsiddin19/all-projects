"""Parol hashlash, login rate-limit va yozuv endpoint'lari uchun auth gate."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request

from .config import settings
from .errors import ApiError
from .owner import is_authenticated

# --- Parol hashlash ---------------------------------------------------------
# bcrypt to'g'ridan-to'g'ri ishlatiladi (passlib 1.7.x bcrypt 4.1+ bilan mos emas edi —
# "password cannot be longer than 72 bytes" xatosi berardi). bcrypt PHP `password_hash($2y$)`
# hash'larini ham tekshiradi. bcrypt algoritmi 72 baytdan ortig'ini e'tiborsiz qoldiradi.
import bcrypt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- Login rate-limit (oddiy in-memory) -------------------------------------
_login_attempts: dict[str, deque[float]] = defaultdict(deque)


def check_login_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = settings.LOGIN_WINDOW_SECONDS
    bucket = _login_attempts[ip]

    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= settings.LOGIN_MAX_ATTEMPTS:
        raise ApiError(
            "Juda ko'p urinish. Iltimos bir necha daqiqadan so'ng qayta urinib ko'ring.",
            status=429,
        )
    bucket.append(now)


def clear_login_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    _login_attempts.pop(ip, None)


# --- Yozuv endpoint'lari uchun gate -----------------------------------------

# --- Umumiy so'rov cheklovi (945MB RAM'li serverni himoya qiladi) --------------
# Login rate-limit'dan alohida: u faqat parol tanlashga qarshi, bu esa umuman
# so'rov toshqiniga (bir IP dan minglab so'rov) qarshi.
_req_hits: dict[str, deque[float]] = defaultdict(deque)
_last_sweep = [0.0]


def check_request_rate(request: Request) -> None:
    limit = settings.RATE_LIMIT_REQUESTS
    if limit <= 0:
        return
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Vaqti-vaqti bilan eski IP yozuvlarini tozalaymiz (xotira cheksiz o'smasin)
    if now - _last_sweep[0] > 300:
        _last_sweep[0] = now
        for key in [k for k, v in _req_hits.items() if not v or now - v[-1] > window]:
            _req_hits.pop(key, None)

    bucket = _req_hits[ip]
    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= limit:
        raise ApiError("Juda ko'p so'rov yuborildi. Biroz kutib turing.", status=429)
    bucket.append(now)


def require_write_access(request: Request) -> None:
    """Mutatsiya qiluvchi endpoint'lar uchun. REQUIRE_AUTH=True bo'lsa login talab qilinadi.

    Bu — PHP versiyasidagi eng katta kamchilikni (yozuv endpoint'larida umuman auth yo'q)
    to'g'irlaydi.
    """
    if not settings.REQUIRE_AUTH:
        return
    if not is_authenticated(request):
        raise ApiError("Bu amal uchun tizimga kirishingiz kerak.", status=401)
