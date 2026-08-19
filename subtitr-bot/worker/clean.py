"""Whisper "gallyutsinatsiya" filtri — soxta matnlarni tozalaydi.

Whisper (ayniqsa jimlik/musiqa qismlarida) o'qitilgan ma'lumotidan "eshitgan"
soxta qatorlar chiqaradi: subtitr-krediti ("Субтитры подготовил…"), kanalga
obuna chaqiriqlari, "DimaTorzok" (rus Whisper'ida eng ko'p uchraydigan soxta
ism), [Music]/♪ kabi SFX belgilari, BOSH-HARFLI sahna izohlari ("ТРЕВОЖНАЯ
МУЗЫКА"), va ketma-ket takror. Bular subtitrga ham, lug'atga ham tushmasin.

Desktop ilovadagi haqiqiy kinolarda sinovdan o'tgan filtrlarning botga ko'chirilgani.
`clean_segments(segments, words)` — tozalangan (segments, words) qaytaradi:
olib tashlangan segment vaqt oraliqlaridagi so'zlar `words` dan ham chiqariladi
(lug'at/dual_vocab soxta so'z olmasin).
"""
from __future__ import annotations

import re

# Soxta subtitr-krediti / obuna chaqiriqlari / tarjima-krediti (ko'p tilli).
_HALLUCINATION_RE = re.compile(
    r"(субтитры?\s+(подготовил|сделал|создавал|редактор|от)"
    r"|субтитры?\s+делал"
    r"|dima\s*torzok|дима\s*торж[ое]к"
    r"|amara\.org|subtitles?\s+by|subs?\s+by|translated\s+by|captions?\s+by"
    r"|подписывайтесь|подписаться|ставьте\s+лайк"
    r"|subscribe|like\s+and\s+subscribe|thanks?\s+for\s+watching"
    r"|продолжение\s+следует)",
    re.IGNORECASE,
)

# SFX / musiqa belgilari: [Music], (music), ♪, ♫, [Applause], [Laughter] va h.k.
_SFX_MARKER_RE = re.compile(
    r"^\s*[\[\(].*[\]\)]\s*$"                       # butun qator [..] yoki (..)
    r"|^[♪♫➤\-–—.\s]+$"                              # faqat nota/tire/nuqta
    r"|(музыка|аплодисменты|смех|интригующая|тревожная|напряжённая)",
    re.IGNORECASE,
)

# BOSH-HARFLI sahna izohi (2-6 so'z, BUTUNLAY katta harf) = SFX/scena caption,
# dialog emas. Kirill va lotin.
_ALLCAPS_CYR_RE = re.compile(r"^[А-ЯЁ][А-ЯЁ\s\-—]{2,60}$")
_ALLCAPS_LAT_RE = re.compile(r"^[A-Z][A-Z\s\-—]{2,60}$")


def _is_allcaps_caption(text: str) -> bool:
    t = text.strip().strip(".!?…")
    if not t or " " not in t:
        return False  # bitta so'z bo'lsa dialog bo'lishi mumkin (aббревiatura emas)
    words = t.split()
    if not (2 <= len(words) <= 6):
        return False
    return bool(_ALLCAPS_CYR_RE.match(t) or _ALLCAPS_LAT_RE.match(t))


def _is_hallucination(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if _HALLUCINATION_RE.search(t):
        return True
    # SFX marker faqat butun qator shunday bo'lsa (dialog ichidagi so'z emas)
    stripped = t.strip("♪♫ ")
    if _SFX_MARKER_RE.match(t) and len(stripped) <= 40:
        return True
    if _is_allcaps_caption(t):
        return True
    return False


def clean_segments(
    segments: list[dict], words: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Gallyutsinatsiya/SFX/takror qatorlarni olib tashlaydi.

    Qaytaradi: (tozalangan_segments, tozalangan_words). Olib tashlangan
    segment vaqt oraliqlaridagi so'zlar `words` dan ham chiqariladi."""
    kept: list[dict] = []
    removed_ranges: list[tuple[float, float]] = []
    prev_norm: str | None = None

    for seg in segments:
        text = (seg.get("text") or "").strip()
        norm = re.sub(r"\s+", " ", text.lower())
        drop = _is_hallucination(text) or (norm and norm == prev_norm)
        if drop:
            removed_ranges.append(
                (float(seg.get("start", 0.0)), float(seg.get("end", 0.0)))
            )
            continue
        kept.append(seg)
        prev_norm = norm

    if not removed_ranges or not words:
        return kept, words

    def _in_removed(w: dict) -> bool:
        ws = float(w.get("start", 0.0))
        we = float(w.get("end", ws))
        mid = (ws + we) / 2.0
        for rs, re_ in removed_ranges:
            if rs <= mid <= re_:
                return True
        return False

    kept_words = [w for w in words if not _in_removed(w)]
    return kept, kept_words
