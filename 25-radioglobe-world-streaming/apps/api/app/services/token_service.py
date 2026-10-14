"""Oqim uchun imzolangan, muddatli token.

Token proxy'ga "bu stream_id ni berish mumkin" deb ishonch bildiradi.
Imzo stream_id ga BOG'LANGAN — bitta oqim uchun olingan token boshqasiga
ishlamaydi.
"""

import hashlib
import hmac
import time

from app.config import settings


def generate_stream_token(stream_id: int, ttl_seconds: int | None = None) -> str:
    ttl = ttl_seconds if ttl_seconds is not None else settings.STREAM_TOKEN_TTL
    expires_at = int(time.time()) + ttl
    message = f"{stream_id}:{expires_at}".encode("utf-8")
    sig = hmac.new(
        settings.PROXY_SECRET_KEY.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return f"{expires_at}.{sig}"


def verify_stream_token(stream_id: int, token: str) -> bool:
    try:
        expires_raw, provided_sig = token.split(".", 1)
        expires_at = int(expires_raw)
    except (ValueError, AttributeError):
        return False

    if time.time() > expires_at:
        return False

    expected_sig = hmac.new(
        settings.PROXY_SECRET_KEY.encode("utf-8"),
        f"{stream_id}:{expires_at}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # compare_digest — vaqt bo'yicha hujumdan himoya
    return hmac.compare_digest(provided_sig, expected_sig)


def build_play_url(stream) -> str:
    """Brauzer to'g'ridan-to'g'ri ishlatadigan manzil.

    needs_proxy=False bo'lsa ham HTTPS shart: HTTP manzil HTTPS sahifada
    mixed-content sifatida bloklanadi, shuning uchun bunday oqim baribir
    proxy orqali beriladi.
    """
    direct_ok = (not stream.needs_proxy) and bool(stream.is_https)
    if direct_ok:
        return stream.url_resolved or stream.url
    return f"{settings.PROXY_BASE_URL}/{stream.id}?t={generate_stream_token(stream.id)}"
