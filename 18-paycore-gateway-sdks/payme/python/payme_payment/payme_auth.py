"""Payme'ning Basic Auth so'rovini tekshirish.

Click'dan farqli o'laroq, Payme har bir so'rovni imzo (sign_string) bilan
emas, oddiy HTTP Basic Authentication bilan tasdiqlaydi:

    Authorization: Basic base64("Paycom:MAXFIY_KALIT")

Login har doim "Paycom" (yoki kabinetda o'zgartirilgan bo'lsa, shu qiymat).
Parol — kabinetdagi kassa uchun berilgan maxfiy kalit.

Bu faylga tegishingiz shart emas.
"""

from __future__ import annotations

import base64
import binascii
import hmac

from .payme_config import PaymeConfig


def check_auth(authorization_header: str | None, config: PaymeConfig) -> bool:
    """`Authorization` sarlavhasini tekshiradi.

    Login va parol vaqt bo'yicha barqaror (timing-safe) solishtiriladi —
    oddiy `==` parolni belgima-belgi topib olish hujumiga yo'l ochadi.
    """
    if not authorization_header or not authorization_header.startswith("Basic "):
        return False

    token = authorization_header[len("Basic "):].strip()

    try:
        decoded = base64.b64decode(token, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return False

    login, _, password = decoded.partition(":")
    if not password:
        return False

    login_ok = hmac.compare_digest(login.encode(), config.merchant_login.encode())
    password_ok = hmac.compare_digest(password.encode(), config.secret_key.encode())

    return login_ok and password_ok
