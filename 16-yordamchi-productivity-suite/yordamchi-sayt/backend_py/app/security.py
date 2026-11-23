"""Parol hashlash, rate-limit, auth gate va xavfsizlik audit jurnali.

Bu modul — ruxsat tekshiruvining YAGONA MANBASI. Ilgari `_require_admin`
beshta handler'da (quiz, dictionary, misc, language_topics, users) qo'lda
ko'chirilgan edi, holbuki `google_auth.is_admin_email()` allaqachon mavjud.
Oqibati: ruxsat mantig'iga har o'zgarish olti joyni talab qilardi va bittasi
e'tibordan chetda qolsa — oddiy foydalanuvchi admin amalini bajarardi.
Aynan shunday teshik 2026-09-08 da topilgan (quiz bazalarini o'chirish).
Endi tekshiruv faqat shu yerda — va shu sababli xavfsizlik logi ham
avtomatik, har chaqiruv uchun alohida yozilmaydi.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import Request

from .config import settings
from .errors import ApiError
from .google_auth import is_admin_email
from .owner import is_authenticated

# --- Xavfsizlik audit jurnali (STRIDE R — Repudiation) ----------------------
# Ilgari 403/401/429 FAQAT foydalanuvchiga qaytarilardi va hech qayerda iz
# qolmasdi — ya'ni buzilish bo'lsa "nima bo'lganini" tiklash imkoni yo'q edi.
# Handler'i `main.py` da ulanadi (`security.log` + journalctl).
security_logger = logging.getLogger("yordamchi.security")


def client_ip(request: Request) -> str:
    """Haqiqiy mijoz IP'si. nginx proxy ortida `request.client` — localhost."""
    fwd = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if fwd:
        return fwd
    return request.client.host if request.client else "unknown"


def log_security_event(request: Request, event: str, detail: str = "") -> None:
    """Rad etilgan urinishni jurnalga yozadi: kim, qayerdan, nimaga urindi."""
    security_logger.warning(
        "%s ip=%s email=%s role=%s action=%s path=%s%s",
        event,
        client_ip(request),
        (request.session.get("doktor_email") or "-"),
        (request.session.get("role") or "-"),
        (request.query_params.get("action") or "-"),
        request.url.path,
        f" {detail}" if detail else "",
    )

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
    ip = client_ip(request)
    now = time.time()
    window = settings.LOGIN_WINDOW_SECONDS
    bucket = _login_attempts[ip]

    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= settings.LOGIN_MAX_ATTEMPTS:
        log_security_event(request, "LOGIN_RATE_LIMIT",
                           f"attempts={len(bucket)} window={window}s")
        raise ApiError(
            "Juda ko'p urinish. Iltimos bir necha daqiqadan so'ng qayta urinib ko'ring.",
            status=429,
        )
    bucket.append(now)


def clear_login_rate_limit(request: Request) -> None:
    ip = client_ip(request)
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
    ip = client_ip(request)
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
        log_security_event(request, "REQUEST_RATE_LIMIT", f"limit={limit}/{window}s")
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
        log_security_event(request, "UNAUTHENTICATED")
        raise ApiError("Bu amal uchun tizimga kirishingiz kerak.", status=401)


# --- Admin ruxsati — YAGONA MANBA ------------------------------------------

def is_admin(request: Request) -> bool:
    """Sessiya admin huquqiga egami.

    Ikki yo'l bilan admin bo'ladi: sessiyadagi `role` (kirish kodi orqali
    kirganda qo'yiladi) yoki `.env` dagi `ALLOWED_EMAILS` ro'yxati
    (`is_admin_email`). Ikkinchisi birlamchi: admin `foydalanuvchilar`
    jadvalida turmaydi.
    """
    email = (request.session.get("doktor_email") or "").strip().lower()
    return request.session.get("role") == "admin" or is_admin_email(email)


def require_admin(
    request: Request,
    message: str = "Faqat administrator o'zgartira oladi.",
) -> None:
    """Admin bo'lmasa 403 va xavfsizlik jurnaliga yozuv.

    Bu funksiya 403 ni log bilan BIRGA beradi — shuning uchun chaqiruv
    joylarida loglashni takrorlash kerak emas va unutib qo'yish mumkin emas.
    """
    if is_admin(request):
        return
    log_security_event(request, "UNAUTHORIZED_ADMIN")
    raise ApiError(message, status=403)
