"""Groq Whisper orqali audio -> matn (segmentlar bilan).

Lokal whisper o'rniga Groq API ishlatamiz: tez va aniqroq (large-v3).
Bu funksiya sinxron (CPU/tarmoq bilan ishlaydi) — pipeline uni
asyncio.to_thread ichida chaqiradi, shunda bot bloklanmaydi.

Uzun audio (TRANSCRIBE_CHUNK_SECONDS dan katta) bo'laklarga bo'linib
PARALLEL transkripsiya qilinadi — 1-2 soatlik kinoda ancha tezroq va Groq
fayl-hajm/limitiga urilib qolmaydi. Bo'lak vaqtlari ofset bilan qo'shiladi.

Xato holati: tarmoq uzilishi, 429 (rate-limit), 5xx (server) —
avtomatik 3 marta qayta urinadi (5s / 10s oraliq).
"""
from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import groq as groq_lib
from groq import Groq

from config import settings
from worker.ffmpeg_utils import probe_duration, split_audio

logger = logging.getLogger(__name__)

_client: Groq | None = None

# Til bo'yicha Whisper "prompt" — modelni to'g'ri imlo/uslubga yo'naltiradi.
# O'zbek (kam resursli til) uchun ayniqsa muhim: o', g', diniy iboralar.
_LANG_PROMPT = {
    "uz": (
        "O'zbek tilidagi suhbat. To'g'ri imlo bilan yoz (o', g', sh, ch, ng): "
        "bo'ladi, o'zbek, to'g'ri, yo'q, kerak, qiladi, Alloh, payg'ambar, "
        "inshaalloh, mustaqillik, rivojlanish."
    ),
}

# Qayta urinish parametrlari
_MAX_ATTEMPTS = 3
_RETRY_WAITS = [5, 10]  # 1-xato: 5s, 2-xato: 10s

# Qayta urinish kerak bo'lgan xatolar
_RETRYABLE = (
    groq_lib.RateLimitError,
    groq_lib.APIConnectionError,
    groq_lib.InternalServerError,
    groq_lib.APITimeoutError,
)


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _seg_value(seg: Any, key: str, default: Any = None) -> Any:
    """Groq segmenti dict yoki obyekt bo'lishi mumkin — ikkalasini ham qo'llaydi."""
    if isinstance(seg, dict):
        return seg.get(key, default)
    return getattr(seg, key, default)


def _call_once(client: Groq, fname: str, data: bytes, base_kwargs: dict) -> Any:
    """Bir urinish: word+segment → muvaffaqiyatsiz bo'lsa faqat segment."""
    try:
        return client.audio.transcriptions.create(
            file=(fname, data),
            timestamp_granularities=["word", "segment"],
            **base_kwargs,
        )
    except _RETRYABLE:
        raise  # tashqi retry ushlasin
    except Exception:
        # Word timestamp qo'llanmasa — oddiy format bilan qaytamiz
        return client.audio.transcriptions.create(file=(fname, data), **base_kwargs)


def _transcribe_bytes(fname: str, data: bytes, base_kwargs: dict) -> Any:
    """Bir audio (bytes) ni retry bilan transkripsiya qiladi — xom resp qaytaradi."""
    client = _get_client()
    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return _call_once(client, fname, data, base_kwargs)
        except _RETRYABLE as exc:
            last_exc = exc
            if attempt < _MAX_ATTEMPTS - 1:
                wait = _RETRY_WAITS[attempt]
                logger.warning(
                    "Groq vaqtincha xato (urinish %d/%d, %ds kutiladi): %s",
                    attempt + 1, _MAX_ATTEMPTS, wait, exc,
                )
                time.sleep(wait)
            else:
                logger.error("Groq %d urinishdan keyin ham xato: %s", _MAX_ATTEMPTS, exc)
                raise
        except Exception:
            raise  # qayta urinish kerak bo'lmagan xato (400 Bad Request va h.k.)
    if last_exc:
        raise last_exc


def _refine_language(detected: str, segments: list[dict]) -> str:
    """Whisper aniqlagan tilni matn ALIFBOSI bilan tekshiradi (Task 16).

    Whisper qisqa/aralash klipda tilni chalkashtirishi mumkin (masalan ruscha
    nutqni boshqa kirill tili deb, yoki teskarisi). Matnning katta qismi kirill
    bo'lsa-yu, aniqlangan til kirill EMAS deb belgilangan bo'lsa — 'ru' ga
    to'g'rilaymiz; lotin ko'p bo'lsa-yu til lotin emas bo'lsa — 'en'. O'zbek
    (uz) ikkala holatда ham saqlanadi (lotin ham, kirill ham bo'lishi mumkin)."""
    text = " ".join(s.get("text", "") for s in segments[:60])
    cyr = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    lat = sum(1 for c in text.lower() if "a" <= c <= "z")
    total = cyr + lat
    if total < 20:
        return detected  # juda kam matn — ishonchsiz, tegmaymiz
    if cyr / total > 0.6 and detected not in ("ru", "uz"):
        return "ru"
    if lat / total > 0.6 and detected not in ("en", "uz"):
        return "en"
    return detected


def _parse_response(resp: Any, offset: float = 0.0) -> tuple[list[dict], list[dict], str]:
    """Groq javobidan (segments, words, detected) chiqaradi; vaqtlarga ofset qo'shadi."""
    detected = (_seg_value(resp, "language", "") or "").strip().lower()

    segments: list[dict] = []
    for seg in (_seg_value(resp, "segments", []) or []):
        text = (_seg_value(seg, "text", "") or "").strip()
        if not text:
            continue
        segments.append(
            {
                "start": float(_seg_value(seg, "start", 0.0) or 0.0) + offset,
                "end": float(_seg_value(seg, "end", 0.0) or 0.0) + offset,
                "text": text,
            }
        )

    words: list[dict] = []
    for w in (_seg_value(resp, "words", []) or []):
        wt = (_seg_value(w, "word", "") or "")
        if not wt.strip():
            continue
        words.append(
            {
                "word": wt,
                "start": float(_seg_value(w, "start", 0.0) or 0.0) + offset,
                "end": float(_seg_value(w, "end", 0.0) or 0.0) + offset,
            }
        )
    return segments, words, detected


def _transcribe_chunk(path: str, offset: float, base_kwargs: dict) -> tuple[list[dict], list[dict], str]:
    """Bitta bo'lak faylni o'qib transkripsiya qiladi (parallel ishchi uchun)."""
    with open(path, "rb") as f:
        data = f.read()
    resp = _transcribe_bytes(os.path.basename(path), data, base_kwargs)
    return _parse_response(resp, offset)


def transcribe(audio_path: str, language: str | None) -> tuple[list[dict], list[dict], str]:
    """Audio faylni subtitr segment va so'zlariga aylantiradi.

    language: "ru" / "en" / "uz" yoki None/"auto" (AI o'zi aniqlaydi).
    Qaytaradi: (segmentlar, so'zlar, aniqlangan_til)
    """
    base_kwargs: dict[str, Any] = {
        "model": settings.whisper_model,
        "response_format": "verbose_json",
    }
    if language and language != "auto":
        base_kwargs["language"] = language
        if language in _LANG_PROMPT:
            base_kwargs["prompt"] = _LANG_PROMPT[language]

    chunk_secs = settings.transcribe_chunk_seconds
    duration = probe_duration(audio_path) if chunk_secs > 0 else 0.0

    forced = language and language != "auto"

    # Qisqa audio (yoki bo'lish o'chiq) — bitta chaqiruv (eski xatti-harakat).
    if chunk_secs <= 0 or duration <= chunk_secs * 1.5:
        with open(audio_path, "rb") as f:
            data = f.read()
        resp = _transcribe_bytes(os.path.basename(audio_path), data, base_kwargs)
        segs, words, det = _parse_response(resp, 0.0)
        if not forced:
            det = _refine_language(det, segs)
        return segs, words, det

    # Uzun audio — bo'laklarga bo'lib PARALLEL transkripsiya.
    chunks = split_audio(audio_path, chunk_secs)
    if len(chunks) <= 1:
        with open(audio_path, "rb") as f:
            data = f.read()
        resp = _transcribe_bytes(os.path.basename(audio_path), data, base_kwargs)
        segs, words, det = _parse_response(resp, 0.0)
        if not forced:
            det = _refine_language(det, segs)
        return segs, words, det

    logger.info(
        "Uzun audio (%.0fs) %d bo'lakka bo'linib parallel transkripsiya qilinmoqda",
        duration, len(chunks),
    )
    results: list[tuple[list[dict], list[dict], str]] = [([], [], "")] * len(chunks)
    workers = max(1, min(settings.transcribe_parallel, len(chunks)))
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {
                ex.submit(_transcribe_chunk, path, off, base_kwargs): idx
                for idx, (path, off) in enumerate(chunks)
            }
            for fut in futures:
                idx = futures[fut]
                results[idx] = fut.result()  # xato bo'lsa butun ish to'xtaydi
    finally:
        # Bo'lak fayllarini tozalaymiz (asl audioga tegmaymiz)
        for path, off in chunks:
            if path != audio_path:
                try:
                    os.remove(path)
                except OSError:
                    pass

    all_segments: list[dict] = []
    all_words: list[dict] = []
    detected = ""
    for segs, words, det in results:
        all_segments.extend(segs)
        all_words.extend(words)
        if not detected and det:
            detected = det
    all_segments.sort(key=lambda s: s["start"])
    all_words.sort(key=lambda w: w["start"])
    if not forced:
        detected = _refine_language(detected, all_segments)
    return all_segments, all_words, detected
