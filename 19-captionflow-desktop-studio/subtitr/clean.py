"""Soxta matnni tozalash va subtitr bo'laklarini moslash."""
from __future__ import annotations

import bisect
import os
import re

from .core import Segment, Word, _env_float, normalize_word


# --- #2: Whisper "hallucination" (soxta matn) filtri ------------------------
# Whisper musiqa/jim sahnalarda takroriy yoki soxta matn chiqaradi. Ularni
# tozalaymiz (faqat transkripsiya natijasiga; tayyor .srt ga tegmaymiz).
# Whisper sukunatda yoki musiqa ustida shu iboralarni "eshitib" qo'yadi —
# ular hech qachon aytilmagan, shuning uchun subtitrga tushmasligi kerak.
HALLUCINATION_RE = [
    re.compile(r"amara\.org|opensubtitles|subscene|addic7ed", re.I),
    re.compile(r"subtitles?\s+by|субтитры\s+(?:подготовил|сделал|от)|редактор\s+субтитров", re.I),
    re.compile(r"sous-titres\s+(?:réalisés|par)|sottotitoli\s+(?:e\s+revisione|a\s+cura)|untertitel(?:ung)?\s+(?:von|im\s+auftrag)", re.I),
    re.compile(r"продолжение\s+следует|thanks?\s+for\s+watching|thank\s+you\s+for\s+watching", re.I),
    re.compile(r"подписывайтесь\s+на\s+канал|ставьте\s+лайк|like\s+and\s+subscribe|請不吝|字幕", re.I),
    re.compile(r"dimatorzok|редактор\s+субтитров\s+[А-ЯЁ]\.|корректор\s+[А-ЯЁ]\.", re.I),
    re.compile(r"^\s*\[?\s*(music|музыка|музика|applause|аплодисменты|laughter|смех)\s*\]?\s*$", re.I),
    re.compile(r"(?:https?://|www\.)\S+", re.I),
    re.compile(r"^[\s♪♫🎵.,!?\-–—…]*$"),
]

# Model nutqni eshitmaganda o'qitish ma'lumotlaridan shu "bo'sh joy
# to'ldiruvchi" iboralarni qaytaradi. Ular butun qatorni egallaydi — shuning
# uchun naqsh qatorning boshidan oxirigacha mos kelishi shart, aks holda
# "Девушки отдыхают на пляже" kabi haqiqiy gap ham o'chib ketadi.
STOCK_PHRASE_RE = [
    re.compile(r"^\W*девушк\w*\s+(?:отдыха\w*|отход\w*)\W*$", re.I),
    re.compile(r"^\W*спасибо\s+за\s+(?:просмотр|внимание)\W*$", re.I),
    re.compile(r"^\W*спасибо,?\s+что\s+смотр\w+(\s+\w+){0,2}\W*$", re.I),
    re.compile(r"^\W*подпис\w+(\s+(?:на|наш\w*|канал|нас))*\W*$", re.I),
    re.compile(r"^\W*продолжение\s+в\s+следующей\s+серии\W*$", re.I),
    re.compile(r"^\W*(?:до\s+новых\s+встреч|всем\s+пока)\W*$", re.I),
    re.compile(r"^\W*(?:bye\s*bye|see\s+you\s+next\s+time)\W*$", re.I),
]

# Qator ichida takrorlangan so'z ("... dey dey dey dey.") — Whisper tsikli.
# Butun qatorni o'chirib yubormaymiz: aytilgan qismi qoladi, takror olib tashlanadi.
REPEAT_RUN_RE = re.compile(r"\b(\w+)(?:[\s,.!?…-]+\1\b){2,}", re.I | re.U)


def collapse_repeats(text: str) -> str:
    """Ketma-ket 3+ marta takrorlangan so'zni bittaga tushiradi."""
    return REPEAT_RUN_RE.sub(lambda m: m.group(1), text)


# Tovush izohi ("ДИНАМИЧНАЯ МУЗЫКА") — Whisper uni butunlay bosh harf bilan
# yozadi; shu ikki belgi (bosh harf + kalit so'z) birga kelsa, bu aytilgan gap
# emas. "Музыка была прекрасной" kabi haqiqiy gaplarda kichik harflar bor.
ANNOTATION_WORD_RE = re.compile(r"музык|аплодисмент|смех|music|applause|laughter|звучит", re.I)


def is_sound_annotation(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters or any(c.islower() for c in letters):
        return False
    return bool(ANNOTATION_WORD_RE.search(text))


def is_hallucination(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 1:
        return True
    if any(rx.search(t) for rx in HALLUCINATION_RE):
        return True
    if is_sound_annotation(t):
        return True
    return any(rx.match(t) for rx in STOCK_PHRASE_RE)


def clean_transcription(segments: list[Segment]) -> list[Segment]:
    """Soxta matn va takrorlangan qatorlarni olib tashlaydi.

    Whisper tsiklga tushganda bitta qatorni o'nlab marta qaytaradi — ular
    ketma-ket ham, oralatib ham kelishi mumkin, shuning uchun ketma-ketligidan
    tashqari umumiy takror soni ham cheklanadi."""
    max_repeat = max(1, int(os.getenv("SUBTITR_MAX_REPEAT", "3")))
    window = _env_float("SUBTITR_REPEAT_WINDOW", 30.0)
    recent: dict[str, list[float]] = {}
    out: list[Segment] = []
    for seg in segments:
        text = " ".join((seg.text or "").split())
        if is_hallucination(text):
            continue
        text = collapse_repeats(text)
        norm = text.lower()
        # Takror chegarasi faqat qisqa vaqt oynasida ishlaydi: Whisper tsikli
        # bitta joyda to'planadi, "Ha." kabi tabiiy takrorlanuvchi gaplar esa
        # film bo'ylab tarqoq keladi — ularni o'chirish nutqni yo'qotish bo'ladi.
        times = [t for t in recent.get(norm, []) if seg.start - t <= window]
        if len(times) >= max_repeat:
            recent[norm] = times
            continue
        times.append(seg.start)
        recent[norm] = times
        out.append(Segment(seg.start, seg.end, text))
    return out


def filter_words(words: list[Word], segments: list[Segment]) -> list[Word]:
    """Lug'at uchun so'zlarni tozalangan subtitrga moslaydi.

    `clean_transcription` olib tashlagan (soxta) bo'laklardagi so'zlar lug'atga
    tushib qolmasligi kerak — aks holda lug'atda hech kim aytmagan so'zlar
    paydo bo'ladi."""
    if not words or not segments:
        return []
    spans = sorted(((s.start, s.end) for s in segments), key=lambda x: x[0])
    starts = [x[0] for x in spans]
    tol = _env_float("SUBTITR_WORD_TOLERANCE", 0.2)
    out: list[Word] = []
    for w in words:
        if is_hallucination(w.word) or len(normalize_word(w.word)) < 2:
            continue
        i = bisect.bisect_right(starts, w.start + tol) - 1
        if i < 0:
            continue
        lo, hi = spans[i]
        # So'z butunlay shu bo'lak ichida bo'lishi kerak — chegaraga tegib
        # turgan (o'chirilgan bo'lakdan qolgan) so'zlar o'tib ketmasin.
        if lo - tol <= w.start and w.end <= hi + tol:
            out.append(w)
    return out


# --- #3: subtitrlarni aqlli birlashtirish/bo'lish ---------------------------

def _split_text(text: str, limit: int) -> list[str]:
    """Uzun matnni gap/vergul/probel chegarasida <= limit bo'laklarga bo'ladi."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while len(rest) > limit:
        window = rest[:limit + 1]
        cut = -1
        for seps in (".!?", ",;:", " "):
            idxs = [window.rfind(s) for s in seps]
            cut = max(idxs)
            if cut > limit * 0.4:
                break
        if cut <= 0:
            cut = limit
        parts.append(rest[:cut + 1].strip())
        rest = rest[cut + 1:].strip()
    if rest:
        # Juda qisqa "quyruq" (masalan bitta so'z) alohida subtitr bo'lib
        # bir zumga chaqnab o'tmasin — oldingi bo'lakka qo'shib yuboramiz.
        if parts and len(rest) < limit * 0.35:
            parts[-1] = (parts[-1] + " " + rest).strip()
        else:
            parts.append(rest)
    return [p for p in parts if p]


def polish_segments(segments: list[Segment]) -> list[Segment]:
    """Juda qisqa bo'laklarni birlashtiradi, juda uzunlarni tabiiy joyda bo'ladi."""
    if not segments:
        return segments
    max_chars = int(os.getenv("SUB_MAX_CHARS", "84"))
    min_dur = float(os.getenv("SUB_MERGE_MIN_DUR", "0.7"))
    min_chars = int(os.getenv("SUB_MERGE_MIN_CHARS", "12"))
    merge_gap = float(os.getenv("SUB_MERGE_GAP", "0.4"))

    # 1) Qisqa bo'laklarni keyingisi bilan birlashtirish.
    merged: list[Segment] = []
    i = 0
    n = len(segments)
    while i < n:
        seg = segments[i]
        while i + 1 < n:
            nxt = segments[i + 1]
            tiny = (seg.end - seg.start) < min_dur or len(seg.text) < min_chars
            close = (nxt.start - seg.end) < merge_gap
            fits = len(seg.text) + 1 + len(nxt.text) <= max_chars
            if tiny and close and fits:
                seg = Segment(seg.start, nxt.end, (seg.text.rstrip() + " " + nxt.text.lstrip()).strip())
                i += 1
            else:
                break
        merged.append(seg)
        i += 1

    # 2) Uzun bo'laklarni bo'lish (vaqtni belgilar soniga mutanosib taqsimlaymiz).
    #    Faqat matn uzunligi emas, davomiyligi ham hisobga olinadi: VAD nutqni
    #    yirik bo'laklarga yig'ib yuborganda bitta gap ekranda 10-15 soniya
    #    osilib qoladi va aytilayotgan so'z bilan mos kelmaydi.
    max_dur = _env_float("SUB_MAX_DUR", 6.0)
    out: list[Segment] = []
    for seg in merged:
        duration = seg.end - seg.start
        if len(seg.text) <= max_chars and duration <= max_dur:
            out.append(seg)
            continue
        by_chars = -(-len(seg.text) // max_chars)
        by_dur = -(-int(duration * 100) // int(max(0.5, max_dur) * 100)) if duration > 0 else 1
        pieces = max(1, by_chars, by_dur)
        limit = max(12, -(-len(seg.text) // pieces))
        parts = _split_text(seg.text, limit)
        total = sum(len(p) for p in parts) or 1
        dur = seg.end - seg.start
        acc = 0
        for p in parts:
            f0 = acc / total
            acc += len(p)
            f1 = acc / total
            out.append(Segment(seg.start + dur * f0, seg.start + dur * f1, p))
    return out


def enforce_reading_speed(segments: list[Segment]) -> list[Segment]:
    """O'qishga qulay bo'lishi uchun subtitr davomiyligini moslashtiradi:
    minimal ko'rinish vaqti va belgi/sekund (CPS) chegarasi, keyingi subtitrga
    tegmagan holda oxirini cho'zadi. Vaqtlarni buzmaydi (faqat oxirini uzaytiradi)."""
    if not segments:
        return segments
    max_cps = float(os.getenv("SUB_MAX_CPS", "20"))
    min_dur = float(os.getenv("SUB_MIN_DUR", "1.0"))
    gap = 0.08
    out: list[Segment] = []
    for i, seg in enumerate(segments):
        start, end = seg.start, seg.end
        limit = segments[i + 1].start - gap if i + 1 < len(segments) else end + 6.0
        chars = len(seg.text)
        need_cps = chars / max_cps if max_cps > 0 else 0.0
        desired_end = start + max(min_dur, need_cps)
        end = min(max(end, desired_end), max(end, limit))
        if end < start:
            end = start
        out.append(Segment(start, end, seg.text))
    return out
