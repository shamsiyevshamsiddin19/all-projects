"""Transkripsiya keshi va uning imzosi."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .core import CACHE_DIR, Segment, Word, safe_stem


# ---------------------------------------------------------------------------
# Checkpoint / cache — uzun kino uzilib qolsa noldan boshlamaslik uchun.
# Transkripsiya, tarjima va lug'at diskka saqlanadi va qayta ishlashda o'qiladi.
# ---------------------------------------------------------------------------

def cache_dir_for(video: Path) -> Path:
    try:
        st = video.stat()
        sig = f"{video.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    except OSError:
        sig = str(video)
    key = hashlib.sha1(sig.encode("utf-8", "replace")).hexdigest()[:10]
    d = CACHE_DIR / f"{safe_stem(video.name)}_{key}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_enabled() -> bool:
    return os.getenv("SUBTITR_NO_CACHE", "") not in {"1", "true", "yes"}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_json(path: Path, data: Any) -> None:
    try:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# Transkripsiya sozlamalari (VAD, anti-hallucination) o'zgarganda eski kesh
# eski — yomon — natijani abadiy qaytarib turmasligi uchun versiya raqami.
TRANSCRIPTION_CACHE_VERSION = 3

# Kesh faqat versiya bilan emas, transkripsiya sozlamalari bilan ham bog'lanadi:
# VAD/chegara/model o'zgarganda eski (yomon) natija qaytarilib turmasin.
# Transkripsiya mantig'i versiyasi. Natijani yaxshilaydigan o'zgarish
# kiritganda SHUNI OSHIRING — aks holda eski (yomon) natija keshdan
# qaytarilaveradi va tuzatish ko'rinmaydi.
#   2 — yutilgan nutqni topish segmentlar orasidagi teshiklarni ham ko'radi
TRANSCRIPTION_LOGIC_VERSION = "2"

_CACHE_SIGNATURE_KEYS = (
    "WHISPER_MODEL", "WHISPER_VAD", "WHISPER_MAX_NO_SPEECH", "WHISPER_LOGPROB",
    "WHISPER_COMPRESSION_RATIO", "WHISPER_HALLUCINATION_SILENCE",
    "WHISPER_MIN_SILENCE_MS", "WHISPER_SPEECH_PAD_MS", "WHISPER_MAX_WORD_DUR",
    "WHISPER_MAX_WORD_GAP", "GROQ_WHISPER_MODEL",
)


def transcription_signature() -> str:
    raw = "|".join(f"{k}={os.getenv(k, '')}" for k in _CACHE_SIGNATURE_KEYS)
    raw = f"v{TRANSCRIPTION_LOGIC_VERSION}|{raw}"
    return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:12]


def load_transcription(cdir: Path) -> tuple[list[Segment], list[Word], str, str] | None:
    if not _cache_enabled():
        return None
    data = _load_json(cdir / "transcription.json")
    if not isinstance(data, dict) or not data.get("segments"):
        return None
    if int(data.get("v", 1)) != TRANSCRIPTION_CACHE_VERSION:
        return None
    if str(data.get("sig", "")) != transcription_signature():
        return None
    segs = [Segment(float(s[0]), float(s[1]), str(s[2])) for s in data["segments"]]
    words = [Word(float(w[0]), float(w[1]), str(w[2])) for w in data.get("words", [])]
    return segs, words, str(data.get("lang", "")), str(data.get("transcriber", "")) + "+cache"


def save_transcription(cdir: Path, segs: list[Segment], words: list[Word], lang: str, transcriber: str) -> None:
    if not _cache_enabled():
        return
    _save_json(cdir / "transcription.json", {
        "v": TRANSCRIPTION_CACHE_VERSION,
        "sig": transcription_signature(),
        "segments": [[s.start, s.end, s.text] for s in segs],
        "words": [[w.start, w.end, w.word] for w in words],
        "lang": lang,
        "transcriber": transcriber,
    })
