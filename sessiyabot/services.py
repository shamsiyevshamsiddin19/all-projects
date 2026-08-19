"""Biznes yordamchilari — aktivlashtirish kodi, Click havola, normalizatsiya."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlencode

from config import settings

_HWID_RE = re.compile(r"[^A-Za-z0-9]")


def normalize_input(value: str | None) -> str:
    return (value or "").strip()


def normalize_hwid(value: str | None) -> str:
    return _HWID_RE.sub("", normalize_input(value).upper())


def activation_key(hwid: str, base_num: str) -> str:
    """md5(HWID + baza + sir) ning birinchi 8 belgisi (PHP bilan AYNAN mos)."""
    raw = normalize_hwid(hwid) + normalize_input(base_num) + settings.secret_salt
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:8].upper()


def click_merchant_trans_id(payment_id: int) -> str:
    return f"{settings.click_tx_prefix}{int(payment_id)}"


def telegram_bot_url(start_payload: str | None = None) -> str:
    url = f"https://t.me/{settings.bot_username.lstrip('@')}"
    if start_payload:
        return f"{url}?start={start_payload}"
    return url


def click_payment_url(payment_id: int, amount: int) -> str:
    query = {
        "service_id": settings.click_service_id,
        "merchant_id": settings.click_merchant_id,
        "amount": int(amount),
        "transaction_param": click_merchant_trans_id(payment_id),
        "merchant_user_id": settings.click_merchant_user_id,
        "return_url": telegram_bot_url(),
    }
    sep = "&" if "?" in settings.click_base_url else "?"
    return f"{settings.click_base_url}{sep}{urlencode(query)}"
