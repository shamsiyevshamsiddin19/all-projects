"""Subtitr cue (blok) quruvchi — professional standartlar asosida.

Maqsad: subtitr video o'lchamiga moslashsin, ekranni to'ldirmasin va
o'qishga qulay tezlikda almashsin (YouTube/Netflix uslubi).

Asosiy g'oyalar:
- So'z darajasidagi vaqt belgilaridan aniq bloklar quriladi (bo'lmasa,
  segmentlar belgi soniga qarab proporsional bo'linadi).
- Har bir blok video kengligiga moslashgan qator uzunligi (CPL) va
  maksimal 2 qatordan oshmaydi -> ekran to'lib ketmaydi.
- Vaqt o'qish tezligiga (CPS) qarab sozlanadi: matn ko'p bo'lsa uzun
  blok bo'lakларга bo'linib tez almashadi; matn kam bo'lsa kamida MIN_DUR
  ko'rsatiladi (juda tez o'tib ketmaydi).
"""
from __future__ import annotations

import math
import re

# Tinish belgilaridan oldingi ortiqcha bo'shliqni olib tashlash
_PUNCT_RE = re.compile(r"\s+([,.!?;:…»)\]])")
_OPEN_RE = re.compile(r"([(«\[])\s+")

# O'qish tezligi va davomiylik chegaralari (professional standart)
CPS_MAX = 17.0      # belgi/sekund — o'qishning yuqori chegarasi
MIN_DUR = 1.0       # blok kamida shuncha ko'rsatiladi (sekund)
MAX_DUR = 7.0       # blok ko'pi bilan shuncha (Netflix/BBC standarti)
MIN_GAP = 0.08      # ketma-ket bloklar orasidagi minimal tanaffus
PAUSE_SPLIT = 0.6   # so'zlar orasida shundan katta jimlik bo'lsa — yangi blok

_SENTENCE_END = ".!?…"


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def _join_words(group: list[dict]) -> str:
    """So'z bo'laklarini bo'sh joy bilan ulaydi va tinish belgilarini to'g'rilaydi.

    Whisper so'zlari bo'shliqsiz keladi ("National","Park",...) — bo'sh joy bilan
    qo'shamiz, lekin ',' '.' kabi belgilardan oldingi bo'shliqni olib tashlaymiz.
    """
    text = " ".join((w.get("word") or "").strip() for w in group)
    text = _PUNCT_RE.sub(r"\1", text)
    text = _OPEN_RE.sub(r"\1", text)
    return _clean(text)


def compute_layout(width: int, height: int, font_scale: float, dual: bool = False) -> dict:
    """Video SHAKLIGA (vertikal/gorizontal/kvadrat) qarab eng qulay shrift,
    qator uzunligi va joylashuvni avtomatik hisoblaydi.

    - Vertikal (Reels/Shorts/TikTok, 9:16): tor kenglik cheklovchi — shrift
      KENGLIK asosida (mutanosib kattaroq) va pastki UI/izoh ustida tursin
      uchun yuqoriroq joylashtiriladi.
    - Gorizontal (16:9): shrift BALANDLIK asosida, pastda (klassik).
    - Kvadrat (1:1, 4:5, 4:3): ikkisining o'rtasi.
    Foydalanuvchi small/medium/large tanlovi (font_scale) ko'paytuvchi
    sifatida saqlanadi — moslashuv uning ustiga qo'shiladi.
    """
    if dual:
        font_scale *= 0.9
    ar = width / max(1, height)
    if ar <= 0.8:                      # vertikal (9:16, 4:5)
        ref = width
        scale = font_scale * 1.7
        pos_frac = 0.17                # pastdan ~17% — UI/izoh ustida
    elif ar < 1.3:                     # kvadratga yaqin (1:1, 4:3)
        ref = (width + height) / 2.0
        scale = font_scale * 1.2
        pos_frac = 0.10
    else:                              # gorizontal (16:9, 21:9)
        ref = height
        scale = font_scale * 1.25
        pos_frac = 0.06
    font_size = max(18, round(ref * scale))
    margin_lr = max(20, round(width * 0.06))
    usable = max(1, width - 2 * margin_lr)
    # O'rtacha belgi kengligi ~ font * 0.52 (Noto Sans uchun)
    cpl = int(usable / (font_size * 0.52))
    cpl = max(10, min(cpl, 42))
    return {
        "font_size": font_size,
        "cpl": cpl,
        "margin_lr": margin_lr,
        "margin_v": max(20, round(height * pos_frac)),
        "outline": max(2, round(font_size * 0.09)),
        # Yengil soya — murakkab/yorqin fonlarda matn ajralib tursin
        "shadow": max(1, round(font_size * 0.06)),
    }


def build_cues(segments: list[dict], words: list[dict], max_chars: int) -> list[dict]:
    """Segment/so'zlardan vaqt va matnli bloklar ro'yxatini quradi.

    Qaytaradi: [{"start","end","text"}, ...]
    """
    if words:
        cues = _cues_from_words(words, max_chars)
    else:
        cues = _cues_from_segments(segments, max_chars)
    cues = _merge_short(cues, max_chars)
    _fix_timing(cues)
    return [c for c in cues if c["text"]]


def _merge_short(cues: list[dict], max_chars: int) -> list[dict]:
    """Juda qisqa/miltillaydigan bloklarni qo'shni bilan birlashtiradi (anti-flicker).

    Faqat: birlashgan matn ≤max_chars, jimlik PAUSE_SPLIT dan kichik, umumiy
    davomiylik ≤MAX_DUR va oldingi blok gap bilan tugamagan bo'lsa.
    """
    if not cues:
        return cues
    merged = [dict(cues[0])]
    for c in cues[1:]:
        a = merged[-1]
        gap = c["start"] - a["end"]
        combined = len(a["text"]) + 1 + len(c["text"])
        a_ends_sentence = a["text"][-1:] in _SENTENCE_END
        if (
            combined <= max_chars
            and gap < PAUSE_SPLIT
            and (c["end"] - a["start"]) <= MAX_DUR
            and not a_ends_sentence
        ):
            a["text"] = f"{a['text']} {c['text']}".strip()
            a["end"] = c["end"]
        else:
            merged.append(dict(c))
    return merged


def _cues_from_words(words: list[dict], max_chars: int) -> list[dict]:
    cues: list[dict] = []
    cur: list[dict] = []

    def text_of(group: list[dict]) -> str:
        return _join_words(group)

    def flush() -> None:
        if cur:
            cues.append(
                {"start": cur[0]["start"], "end": cur[-1]["end"], "text": text_of(cur)}
            )

    prev_end = None
    for w in words:
        gap = (w["start"] - prev_end) if prev_end is not None else 0.0
        candidate = text_of(cur + [w])
        # Hozirgi blok to'lib qolsa yoki katta jimlik bo'lsa — avval yopamiz
        if cur and (len(candidate) > max_chars or gap > PAUSE_SPLIT):
            flush()
            cur = []
        cur.append(w)
        prev_end = w["end"]
        # Gap tugashi (. ! ?) + blok yetarli uzun bo'lsa — yopamiz
        cur_text = text_of(cur)
        if cur_text[-1:] in _SENTENCE_END and len(cur_text) >= max_chars * 0.5:
            flush()
            cur = []
            prev_end = None
    flush()
    return cues


def _cues_from_segments(segments: list[dict], max_chars: int) -> list[dict]:
    cues: list[dict] = []
    for seg in segments:
        text = _clean(seg.get("text", ""))
        if not text:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        chunks = _split_text(text, max_chars)
        total = sum(len(c) for c in chunks) or 1
        dur = max(end - start, 0.1)
        t = start
        for chunk in chunks:
            ct = dur * (len(chunk) / total)
            cues.append({"start": t, "end": t + ct, "text": chunk})
            t += ct
    return cues


def _split_text(text: str, max_chars: int) -> list[str]:
    """Matnni so'z chegarasida ≤max_chars bo'laklarga ajratadi."""
    words = text.split()
    chunks: list[str] = []
    cur = ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            chunks.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def _fix_timing(cues: list[dict]) -> None:
    """O'qish tezligi, min/max davomiylik va bloklararo tanaffusni sozlaydi."""
    n = len(cues)
    for i, c in enumerate(cues):
        dur = c["end"] - c["start"]
        needed = len(c["text"]) / CPS_MAX
        target = min(MAX_DUR, max(MIN_DUR, needed, dur))
        c["end"] = c["start"] + target
        # Keyingi blok bilan ustma-ust tushmasin
        if i + 1 < n:
            next_start = cues[i + 1]["start"]
            if c["end"] > next_start - MIN_GAP:
                c["end"] = max(c["start"] + 0.4, next_start - MIN_GAP)
