"""Google ID token'ini tekshirish.

NIMA UCHUN KERAK BO'LDI
-----------------------
Eski `google_kirish` mijoz yuborgan `email` va `firebase_uid` ga SHUNCHAKI
ISHONARDI. Ya'ni istalgan odam:

    POST /api  {"amal":"google_kirish","email":"<ega email>","firebase_uid":"x"}

deb yuborib, sayt egasi sifatida sessiya ochib olishi mumkin edi. Emailni
oddiy ro'yxatga solishtirish bu teshikni YOPMAYDI — email hujumchining
o'zidan kelyapti. Shuning uchun mijozdan endi faqat Google IMZOLAGAN ID
token olinadi va u Google'ning o'zida tekshiriladi.

NIMA UCHUN `tokeninfo`, JWT'ni qo'lda ochib emas
-----------------------------------------------
JWT imzosini qo'lda tekshirish (JWKS yuklab olish, kalitni topish, `alg`
ni faqat RS256 bilan cheklash, `aud`/`iss`/`exp` ni solishtirish) —
xavfsizlikda eng ko'p xato qilinadigan joylardan biri: bitta e'tibordan
qolgan tafsilot (masalan `alg: none` ni rad etmaslik) butun himoyani
bekor qiladi. Bu yerda imzoni Google o'zi tekshiradi, bizga faqat javobni
solishtirish qoladi. Kirish kamdan-kam bo'lgani uchun har kirishda bitta
HTTPS so'rov — arzimas narx.
"""

from __future__ import annotations

import time

import httpx

from .config import settings
from .errors import AuthError

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

# Google ID token — bu JWT. Aql bovar qilmaydigan uzunlikdagi satrni
# umuman Google'ga yubormaymiz.
MAX_TOKEN_LEN = 8192


def _truthy(value) -> bool:
    """tokeninfo `email_verified` ni ba'zan "true" satri, ba'zan bool qaytaradi."""
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def verify_google_id_token(token: str) -> dict:
    """Token haqiqiyligini tekshiradi va {email, name, sub} qaytaradi.

    Har qanday shubhada `AuthError` ko'tariladi — ya'ni standart holat
    "kirishga ruxsat yo'q".
    """
    token = (token or "").strip()
    if not token:
        raise AuthError("Google tokeni kelmadi.")
    if len(token) > MAX_TOKEN_LEN:
        raise AuthError("Google tokeni noto'g'ri.")

    if not settings.GOOGLE_CLIENT_ID:
        # Sozlanmagan bo'lsa kirishni OCHIQ qoldirib bo'lmaydi.
        raise AuthError("Google kirishi sozlanmagan (GOOGLE_CLIENT_ID yo'q).")

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(TOKENINFO_URL, params={"id_token": token})
    except Exception:
        raise AuthError("Google bilan bog'lanib bo'lmadi. Qaytadan urinib ko'ring.")

    if resp.status_code != 200:
        raise AuthError("Google tokeni haqiqiy emas.")

    try:
        data = resp.json()
    except Exception:
        raise AuthError("Google javobini o'qib bo'lmadi.")

    # --- Token AYNAN BIZNING saytimiz uchun berilganmi? ---
    # Bu tekshiruvsiz, boshqa saytga berilgan haqiqiy token bilan ham
    # kirib bo'lardi ("token almashtirish" hujumi).
    if str(data.get("aud") or "") != settings.GOOGLE_CLIENT_ID:
        raise AuthError("Token boshqa ilova uchun berilgan.")

    if str(data.get("iss") or "") not in VALID_ISSUERS:
        raise AuthError("Token manbasi noto'g'ri.")

    # tokeninfo muddati o'tgan tokenni o'zi rad etadi; bu ikkinchi to'siq.
    try:
        if int(data.get("exp") or 0) <= int(time.time()):
            raise AuthError("Token muddati tugagan. Qaytadan kiring.")
    except (TypeError, ValueError):
        raise AuthError("Token muddati noto'g'ri.")

    email = str(data.get("email") or "").strip().lower()
    if not email:
        raise AuthError("Google akkauntida email yo'q.")
    if not _truthy(data.get("email_verified")):
        raise AuthError("Google emaili tasdiqlanmagan.")

    return {
        "email": email,
        "name": str(data.get("name") or "").strip() or email.split("@")[0],
        "sub": str(data.get("sub") or "").strip(),
    }


def email_allowed(email: str) -> bool:
    """Faqat ro'yxatdagi egalar. Ro'yxat bo'sh bo'lsa — hech kim."""
    allowed = settings.ALLOWED_EMAILS
    if not allowed:
        return False
    return (email or "").strip().lower() in allowed
