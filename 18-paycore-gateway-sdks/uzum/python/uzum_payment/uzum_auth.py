"""Uzum Bank'ning Basic Auth so'rovini tekshirish.

Payme'ga o'xshab, Uzum Bank ham har bir webhook so'rovini oddiy HTTP Basic
Authentication bilan tasdiqlaydi:

    Authorization: Basic base64("login:parol")

Farqi: Payme'da login doim "Paycom", Uzum'da esa LOGIN HAM, PAROL HAM siz
kabinetda o'zingiz belgilaysiz (ikkalasi ham `.env` da).

Bu faylga tegishingiz shart emas.
"""

from __future__ import annotations

import base64
import binascii
import hmac

from .uzum_config import UzumConfig


def check_auth(authorization_header: str | None, config: UzumConfig) -> bool:
    """`Authorization` sarlavhasini tekshiradi.

    Login va parol vaqt bo'yicha barqaror (timing-safe) solishtiriladi.
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

    login_ok = hmac.compare_digest(login.encode(), config.webhook_login.encode())
    password_ok = hmac.compare_digest(password.encode(), config.webhook_secret.encode())

    return login_ok and password_ok
