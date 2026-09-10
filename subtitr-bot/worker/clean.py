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
# DIQQAT: kalit so'z (музыка, смех...) o'z-o'zidan filtr emas — "Музыка была
# прекрасной" haqiqiy gap. Kalit so'z faqat qavs ichida yoki BOSH HARF bilan
# yozilgan izohda hisobga olinadi.
_SFX_MARKER_RE = re.compile(
    r"^\s*[\[\(].*[\]\)]\s*$"                       # butun qator [..] yoki (..)
    r"|^[♪♫➤\-–—.\s]+$",                             # faqat nota/tire/nuqta
    re.IGNORECASE,
)

# Modelning "bo'sh joy to'ldiruvchi" iboralari: nutq eshitilmaganda o'qitish
# ma'lumotlaridan chiqadi. Naqsh BUTUN qatorga mos kelishi shart — aks holda
# "Девушки отдыхают на пляже" kabi haqiqiy gap ham o'chib ketadi.
_STOCK_PHRASE_RE = [
    re.compile(r"^\W*девушк\w*\s+(отдыха\w*|отход\w*)\W*$", re.I),
    re.compile(r"^\W*спасибо\s+за\s+(просмотр|внимание)\W*$", re.I),
    re.compile(r"^\W*спасибо,?\s+что\s+смотр\w+(\s+\w+){0,2}\W*$", re.I),
    re.compile(r"^\W*(до\s+новых\s+встреч|всем\s+пока)\W*$", re.I),
    re.compile(r"^\W*(bye\s*bye|see\s+you\s+next\s+time)\W*$", re.I),
]

# BOSH-HARFLI sahna izohi (2-6 so'z, BUTUNLAY katta harf) = SFX/scena caption,
# dialog emas. Kirill va lotin.
_ALLCAPS_CYR_RE = re.compile(r"^[А-ЯЁ][А-ЯЁ\s\-—]{2,60}$")
_ALLCAPS_LAT_RE = re.compile(r"^[A-Z][A-Z\s\-—]{2,60}$")


def _is_allcaps_caption(text: str) -> bool:
    t = text.strip()
    # Baqirib aytilgan gap ham bosh harf bilan chiqishi mumkin, lekin u deyarli
    # doim "!" yoki "?" bilan tugaydi; sahna izohida bunday tinish belgisi yo'q.
    if t.endswith(("!", "?")):
        return False
    t = t.strip(".!?…")
    if not t or " " not in t:
        return False  # bitta so'z bo'lsa dialog bo'lishi mumkin (aббревiatura emas)
    words = t.split()
    if not (2 <= len(words) <= 6):
        return False
    return bool(_ALLCAPS_CYR_RE.match(t) or _ALLCAPS_LAT_RE.match(t))


# Qator ichida ketma-ket 3+ marta takrorlangan so'z — Whisper tsikli. Butun
# qatorni o'chirmaymiz: aytilgan qismi qoladi, takror bittaga tushiriladi.
_REPEAT_RUN_RE = re.compile(r"\b(\w+)(?:[\s,.!?…-]+\1\b){2,}", re.I | re.U)


def collapse_repeats(text: str) -> str:
    return _REPEAT_RUN_RE.sub(lambda m: m.group(1), text)


# Bir xil qator shu oyna ichida shuncha martadan ko'p kelsa — tsikl.
_REPEAT_WINDOW = 30.0
_MAX_REPEAT = 3


def is_hallucination(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if _HALLUCINATION_RE.search(t):
        return True
    if any(rx.match(t) for rx in _STOCK_PHRASE_RE):
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
    recent: dict[str, list[float]] = {}

    for seg in segments:
        text = (seg.get("text") or "").strip()
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        norm = re.sub(r"\s+", " ", text.lower())

        drop = is_hallucination(text)
        if not drop and norm:
            # Takror chegarasi faqat qisqa vaqt oynasida ishlaydi: Whisper tsikli
            # bitta joyda to'planadi, "Ha." / "Да." kabi tabiiy takrorlanuvchi
            # gaplar esa film bo'ylab tarqoq keladi va ularni o'chirish —
            # haqiqiy nutqni yo'qotish bo'ladi.
            times = [t for t in recent.get(norm, []) if start - t <= _REPEAT_WINDOW]
            if len(times) >= _MAX_REPEAT:
                recent[norm] = times
                drop = True
            else:
                times.append(start)
                recent[norm] = times

        if drop:
            removed_ranges.append((start, end))
            continue

        collapsed = collapse_repeats(text)
        if collapsed != text:
            seg = {**seg, "text": collapsed}
        kept.append(seg)

    if not removed_ranges or not words:
        return kept, words

    kept_ranges = [
        (float(s.get("start", 0.0)), float(s.get("end", 0.0))) for s in kept
    ]

    def _in(mid: float, ranges: list[tuple[float, float]]) -> bool:
        return any(rs <= mid <= re_ for rs, re_ in ranges)

    def _in_removed(w: dict) -> bool:
        ws = float(w.get("start", 0.0))
        we = float(w.get("end", ws))
        mid = (ws + we) / 2.0
        if not _in(mid, removed_ranges):
            return False
        # Soxta segment uzun oraliqni (masalan 0-30s) egallashi mumkin va
        # uning ichiga haqiqiy gaplar tushib qoladi — saqlangan segmentga ham
        # tegishli so'zni olib tashlamaymiz.
        return not _in(mid, kept_ranges)

    kept_words = [w for w in words if not _in_removed(w)]
    return kept, kept_words
