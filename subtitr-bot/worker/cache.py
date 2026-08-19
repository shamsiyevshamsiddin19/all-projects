"""Transkripsiya keshi (Redis) — bir xil audioni qayta transkripsiya qilmaslik.

Nega kerak: bir foydalanuvchi videoni "tarjima" qilib, keyin "boshqa rejim"
(reuse) yoki xuddi shu videoni qayta yuborsa — Groq Whisper qaytadan
chaqirilardi (sekin + API sarfi). Kesh bilan bir xil audio (SHA256 bo'yicha)
uchun transkripsiya bir marta olinadi va 7 kun saqlanadi.

Kalit — ajratilgan audio faylining hash'i + majburlangan til (source_lang
transkripsiyaga ta'sir qiladi, shuning uchun kalitga kiradi). Manba (upload /
YouTube / Instagram) ahamiyatsiz: bir xil kontent = bir xil audio = bir xil
hash.

Xato bo'lsa (Redis yo'q va h.k.) — jim o'tadi, oddiy transkripsiya ishlaydi.
"""
from __future__ import annotations

import hashlib
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

_TTL = 7 * 24 * 3600   # 7 kun
_redis = None


def _client():
    global _redis
    if _redis is None:
        import redis
        _redis = redis.from_url(settings.celery_broker, socket_timeout=2)
    return _redis


def audio_hash(path: str) -> str:
    """Audio faylning SHA256 hash'i (32 belgi hex). Bo'laklab o'qiydi."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _key(ahash: str, source_lang: str | None) -> str:
    return f"tx:{ahash}:{source_lang or 'auto'}"


def get_transcription(ahash: str, source_lang: str | None):
    """Keshdan (segments, words, detected) qaytaradi yoki topilmasa None."""
    try:
        raw = _client().get(_key(ahash, source_lang))
        if not raw:
            return None
        data = json.loads(raw)
        return data["segments"], data["words"], data["detected"]
    except Exception as exc:
        logger.debug("cache.get_transcription xato: %s", exc)
        return None


def set_transcription(ahash: str, source_lang: str | None, result) -> None:
    """(segments, words, detected) ni keshga yozadi. Xato bo'lsa jim o'tadi."""
    try:
        segments, words, detected = result
        payload = json.dumps(
            {"segments": segments, "words": words, "detected": detected},
            ensure_ascii=False,
        )
        _client().setex(_key(ahash, source_lang), _TTL, payload)
    except Exception as exc:
        logger.debug("cache.set_transcription xato: %s", exc)
