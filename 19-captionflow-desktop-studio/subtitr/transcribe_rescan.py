"""Yutilgan nutqni aniqlash va qayta o'qish qatlami."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from .clean import is_hallucination
from .core import FFMPEG, Segment, Word, _count, _env_float, emit, run
from .media import probe_duration_seconds

RESCAN_MIN_DUR = 10.0
RESCAN_MAX_CPS = 4.0
RESCAN_WINDOW = 12.0
RESCAN_OVERLAP = 6.0
RESCAN_PAD = 3.0
RESCAN_MAX_TOTAL = 180.0
RESCAN_MAX_WINDOWS = 30
RESCAN_EDGE = 0.6
RESCAN_SHIFTS = (2.0, 4.0)
RESCAN_MAX_RETRY = 8
RESCAN_GAP_MIN = 3.0
RESCAN_GAP_SPEECH = 1.5
RESCAN_GAP_MAX_CHECKS = 25

def _mmss(seconds: float) -> str:
    """Soniyani "mm:ss" ko'rinishiga o'giradi (ogohlantirish matnlari uchun)."""
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def seg_density(seg: Segment) -> float:
    """Segment matn zichligi (belgi/sek). Haqiqiy nutq ~10-20, soxta qator <1."""
    return len((seg.text or "").strip()) / max(0.01, seg.end - seg.start)


def suspect_ranges(segments: list[Segment]) -> list[tuple[float, float]]:
    """Nutq yutib yuborilgan bo'lishi mumkin bo'lgan oraliqlar."""
    ranges: list[tuple[float, float]] = []
    for seg in segments:
        if seg.end - seg.start < RESCAN_MIN_DUR or seg_density(seg) > RESCAN_MAX_CPS:
            continue
        if ranges and seg.start - ranges[-1][1] < 1.0:
            ranges[-1] = (ranges[-1][0], seg.end)
        else:
            ranges.append((seg.start, seg.end))

    return ranges_within_budget(ranges)


def ranges_within_budget(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Qayta o'qish xarajatini cheklaydi: eng uzun oraliqlardan boshlab
    `RESCAN_MAX_TOTAL` soniya to'lgunicha oladi."""
    total = 0.0
    picked: list[tuple[float, float]] = []
    for rng in sorted(ranges, key=lambda r: r[1] - r[0], reverse=True):
        span = rng[1] - rng[0]
        if total + span > RESCAN_MAX_TOTAL:
            continue
        picked.append(rng)
        total += span
    return sorted(picked)


def _pcm_window(media: Path, start: float, dur: float) -> Any:
    """Audioning bir bo'lagini 16 kHz mono float massiv qilib o'qiydi.

    Vaqtinchalik fayl yasalmaydi — ffmpeg xom PCM ni to'g'ridan-to'g'ri
    quvurga beradi."""
    import numpy as np

    proc = subprocess.run(
        [
            FFMPEG, "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
            "-i", str(media), "-vn", "-ac", "1", "-ar", "16000",
            "-f", "f32le", "-",
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None
    return np.frombuffer(proc.stdout, dtype=np.float32)


def _speech_seconds_vad(media: Path, start: float, dur: float) -> float | None:
    """Oynada necha soniya NUTQ borligini lokal Silero VAD bilan o'lchaydi.

    Musiqa va shovqinni nutqdan ajratadi — shuning uchun jim yoki musiqali
    bo'shliqqa bekorga Groq so'rovi ketmaydi. VAD ishlamasa None qaytadi."""
    try:
        from faster_whisper.vad import VadOptions, get_speech_timestamps

        audio = _pcm_window(media, start, dur)
        if audio is None or len(audio) < 16000 // 4:
            return 0.0
        opts = VadOptions(min_silence_duration_ms=500, speech_pad_ms=200)
        stamps = get_speech_timestamps(audio, opts, 16000)
        return sum(t["end"] - t["start"] for t in stamps) / 16000.0
    except Exception:
        return None


def _speech_seconds_ffmpeg(media: Path, start: float, dur: float) -> float:
    """VAD bo'lmaganda zaxira o'lchov: jim bo'lmagan vaqt.

    Musiqani nutqdan ajrata olmaydi, shuning uchun ba'zan ortiqcha qayta
    o'qishga olib keladi — lekin nutqni yo'qotgandan ko'ra yaxshiroq."""
    proc = subprocess.run(
        [
            FFMPEG, "-v", "info", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
            "-i", str(media), "-vn",
            "-af", "silencedetect=noise=-33dB:d=0.4", "-f", "null", "-",
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace",
    )
    silence = sum(
        float(m) for m in re.findall(r"silence_duration:\s*([0-9.]+)", proc.stderr or "")
    )
    return max(0.0, dur - silence)


def speech_seconds(media: Path, start: float, dur: float) -> float:
    result = _speech_seconds_vad(media, start, dur)
    if result is None:
        return _speech_seconds_ffmpeg(media, start, dur)
    return result


def swallowed_gap_ranges(
    media: Path, segments: list[Segment], duration: float
) -> list[tuple[float, float]]:
    """Transkripsiya BUTUNLAY o'tkazib yuborgan parchalarni topadi.

    `suspect_ranges()` faqat mavjud segmentlarning ichiga qaraydi (uzun, lekin
    matni siyrak bo'lsa — nutq yutilgan deb hisoblaydi). Groq butun bir
    parchani qaytarmasa esa tekshiradigan segment ham qolmaydi: teshik
    ko'rinmaydi, subtitr esa ekranda o'nlab soniya yo'qolib turadi.

    Shuning uchun segmentlar ORASIDAGI bo'shliqlar ham ko'riladi. Har bir
    bo'shliqda nutq bor-yo'qligi avval lokal VAD bilan tekshiriladi — tabiiy
    pauza, musiqa va titrlar uchun bekorga so'rov ketmasin."""
    segs = sorted(segments, key=lambda s: s.start)
    if not segs:
        return []
    holes: list[tuple[float, float]] = []
    if segs[0].start >= RESCAN_GAP_MIN:
        holes.append((0.0, segs[0].start))
    for cur, nxt in zip(segs, segs[1:]):
        if nxt.start - cur.end >= RESCAN_GAP_MIN:
            holes.append((cur.end, nxt.start))
    if duration > 0 and duration - segs[-1].end >= RESCAN_GAP_MIN:
        holes.append((segs[-1].end, duration))
    if not holes:
        return []

    # Tekshiruvning o'zi ham bepul emas (har biri bitta ffmpeg) — eng uzun
    # teshiklardan boshlaymiz, ular eng ko'p nutq yo'qotadi.
    holes.sort(key=lambda h: h[1] - h[0], reverse=True)
    found: list[tuple[float, float]] = []
    for lo, hi in holes[:RESCAN_GAP_MAX_CHECKS]:
        import sys
        engine = sys.modules.get("subtitr._transcribe_engine")
        speech_check = getattr(engine, "speech_seconds", speech_seconds)
        if speech_check(media, lo, hi - lo) >= RESCAN_GAP_SPEECH:
            found.append((lo, hi))
    return sorted(found)


def rescan_windows(rs: float, re_: float) -> list[float]:
    """Oraliqni USTMA-UST oynalarga bo'ladi (oyna boshlanish nuqtalari)."""
    step = max(1.0, RESCAN_WINDOW - RESCAN_OVERLAP)
    out: list[float] = []
    pos = rs
    while pos < re_ - 0.5:
        out.append(pos)
        pos += step
    return out


def pick_best_segments(cands: list[tuple[Segment, float]]) -> list[tuple[Segment, float]]:
    """Ustma-ust oynalardan kelgan nomzodlardan eng to'liqlarini tanlaydi.

    Matni eng UZUN nomzoddan boshlab olamiz; vaqt bo'yicha unga jiddiy tegib
    turgan qolganlari tashlanadi. Shunda oyna chetida kesilgan yarim jumla
    ("Май ещё долго будет") o'rniga to'liq varianti ("Гена, зима ещё долго
    будет?") saqlanadi."""
    kept: list[tuple[Segment, float]] = []
    for seg, win in sorted(cands, key=lambda c: (len(c[0].text.strip()), seg_density(c[0])), reverse=True):
        dur = max(0.01, seg.end - seg.start)
        if any(
            min(p.end, seg.end) - max(p.start, seg.start) > 0.5 * min(dur, p.end - p.start)
            for p, _w in kept
        ):
            continue
        kept.append((seg, win))
    return sorted(kept, key=lambda c: c[0].start)


def _rescan_one(
    transcribe: "WindowTranscriber",
    media_path: Path,
    language: str,
    start: float,
    dur: float,
    tmp_dir: Path,
) -> tuple[list[Segment], list[Word]]:
    """Bitta oynani kesib olib qayta transkripsiya qiladi.

    Oyna atigi ~12 soniya, ya'ni hajm muammo emas — shuning uchun uni 12 kbit/s
    opus emas, 64 kbit/s mp3 qilib kesamiz. Kuchli siqilish nutqni buzadi va
    aynan shu soxta matnni keltirib chiqaradi (extract_audio izohiga qarang),
    qayta o'qishda esa bizga eng toza audio kerak."""
    part = tmp_dir / f"rescan_{int(start * 1000)}.mp3"
    try:
        proc = run(
            [
                FFMPEG, "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
                "-i", str(media_path),
                "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "libmp3lame", "-b:a", "64k",
                str(part),
            ]
        )
        if proc.returncode != 0 or not part.exists() or part.stat().st_size == 0:
            return [], []
        _count("rescan")
        segs, words, _ = transcribe(part, language, start)
    except Exception:
        return [], []  # bitta oyna tushsa ham butun ish to'xtamasin
    finally:
        part.unlink(missing_ok=True)

    # Soxta qator nomzodlikka ham tushmasin — u haqiqiy jumlaning o'rnini
    # egallab qolishi mumkin
    return [s for s in segs if not is_hallucination(s.text)], words


# Bitta oynani transkripsiya qiladigan funksiya: (fayl, til, siljish) ->
# (bo'laklar, so'zlar, aniqlangan til). Groq ham, lokal model ham shu
# ko'rinishga o'raladi — qayta o'qish mantig'i ikkalasi uchun bitta.
WindowTranscriber = Callable[[Path, str, float], tuple[list[Segment], list[Word], str]]


def rescan_swallowed_speech(
    transcribe: "WindowTranscriber",
    audio_path: Path,
    language: str,
    segments: list[Segment],
    words: list[Word],
    source_media: Path | None = None,
) -> tuple[list[Segment], list[Word]]:
    """Shubhali oraliqlarni qisqa oynalarda qayta o'qib, natijani almashtiradi.

    `source_media` berilsa (asl video/audio) — oynalar o'shandan kesiladi:
    Groq'ga yuborilgan 12 kbit/s opus nutqni allaqachon buzgan bo'ladi.

    SUBTITR_NO_RESCAN=1 bilan butunlay o'chiriladi (tezroq, lekin yutilgan
    nutq tiklanmaydi)."""
    if os.getenv("SUBTITR_NO_RESCAN", "") in {"1", "true", "yes"}:
        return segments, words
    cut_from = source_media if source_media and source_media.exists() else audio_path
    import sys
    engine = sys.modules.get("subtitr._transcribe_engine")
    gap_finder = getattr(engine, "swallowed_gap_ranges", swallowed_gap_ranges)
    ranges = ranges_within_budget(
        suspect_ranges(segments) + gap_finder(cut_from, segments, probe_duration_seconds(cut_from))
    )
    if not ranges:
        return segments, words

    starts: list[float] = []
    for rs, re_ in ranges:
        starts.extend(rescan_windows(max(0.0, rs - RESCAN_PAD), re_ + RESCAN_PAD))
    starts = starts[:RESCAN_MAX_WINDOWS]
    emit("progress", message=f"Nutq yutilgan {len(ranges)} joy qayta o'qilmoqda", progress=0.32)

    cands: list[tuple[Segment, float]] = []
    new_words: list[tuple[Word, float]] = []

    def sweep(points: list[float]) -> None:
        for st in points:
            # Legacy callers monkeypatch this hook through subtitr.transcribe.
            # Resolve it late so the public compatibility seam keeps working.
            import sys
            engine = sys.modules.get("subtitr._transcribe_engine")
            rescanner = getattr(engine, "_rescan_one", _rescan_one)
            segs, wds = rescanner(
                transcribe, cut_from, language, st, RESCAN_WINDOW, audio_path.parent
            )
            cands.extend((s, st) for s in segs)
            new_words.extend((w, st) for w in wds)

    sweep(starts)

    # 2-bosqich: oynaning ENG BOSHIDA turgan segment — jumla chegarada kesilgan
    # degani. Whisper oynani musiqadan emas, nutqdan boshlaganda to'g'ri
    # eshitadi, shuning uchun o'sha joyni bir-ikki soniya oldinroqdan qayta
    # o'qiymiz va to'liqroq variantini olamiz.
    done = {round(st, 2) for st in starts}
    retries: list[float] = []
    for seg, win in cands:
        if seg.start - win > RESCAN_EDGE:
            continue
        for shift in RESCAN_SHIFTS:
            st = max(0.0, win - shift)
            if round(st, 2) in done or st >= win:
                continue
            done.add(round(st, 2))
            retries.append(st)
    if retries:
        sweep(sorted(retries)[:RESCAN_MAX_RETRY])

    # Pad tufayli oraliqdan tashqariga chiqqanlar kerak emas — u yerni asosiy
    # transkripsiya allaqachon to'g'ri o'qigan
    cands = [
        c for c in cands
        if any(rs <= (c[0].start + c[0].end) / 2.0 <= re_ for rs, re_ in ranges)
    ]
    # Uzun, lekin matni siyrak nomzod — nutq emas, musiqa ustidagi soxta qator.
    #
    # Filtr TANLASHDAN OLDIN qo'llanadi. Aks holda butun oynani qoplagan soxta
    # qator ("Нет, Смотрит в шкафу, Нет, Кот Вася смотри." — 12s, 3.6 belgi/sek)
    # matni eng uzun bo'lgani uchun `pick_best_segments` da g'olib chiqadi,
    # ustma-ust tushgan haqiqiy qatorlarni siqib chiqaradi va shundan keyingina
    # o'zi ham tashlanadi — oraliq butunlay bo'sh qoladi.
    cands = [
        c for c in cands
        if c[0].end - c[0].start < RESCAN_MIN_DUR or seg_density(c[0]) > RESCAN_MAX_CPS
    ]
    best = pick_best_segments(cands)
    if not best:
        return segments, words

    spans = {(win, s.start, s.end) for s, win in best}
    kept_new_words = [
        w for w, win in new_words
        if any(win == wn and a - 0.05 <= w.start <= b + 0.05 for wn, a, b in spans)
    ]
    new_segments = [s for s, _win in best]

    # Faqat HAQIQATAN yangi matn topilgan oraliqlar almashtiriladi: bo'sh
    # qaytgan oraliqda eski matn joyida qolsin (yo'qotmaylik).
    replaced = [
        (rs, re_) for rs, re_ in ranges
        if any(rs <= (s.start + s.end) / 2.0 <= re_ for s in new_segments)
    ]

    def outside(start: float, end: float) -> bool:
        mid = (start + end) / 2.0
        return not any(rs <= mid <= re_ for rs, re_ in replaced)

    merged = sorted(
        [s for s in segments if outside(s.start, s.end)] + new_segments,
        key=lambda s: s.start,
    )
    # Qayta o'qilgan oyna qo'shni segmentga tegib ketishi mumkin — ekranda
    # ikkita subtitr bir vaqtda chiqmasin.
    #
    # `Segment` o'zgarmas (frozen), shuning uchun joyida tuzatish emas —
    # ustma-ust tushgan bo'lak yangi obyekt bilan almashtiriladi. Ilgari
    # bu yerda `cur.end = ...` turardi: obyekt kesh orqali ham, sessiya
    # fayli orqali ham o'tgani uchun uni kim o'zgartirganini kuzatish
    # qiyin edi.
    trimmed: list[Segment] = []
    for i, cur in enumerate(merged):
        if i + 1 < len(merged) and cur.end > merged[i + 1].start:
            cur = Segment(cur.start, max(cur.start + 0.2, merged[i + 1].start),
                          cur.text, cur.confidence)
        trimmed.append(cur)
    merged = trimmed
    merged_words = sorted(
        [w for w in words if outside(w.start, w.end)] + kept_new_words,
        key=lambda w: w.start,
    )
    return merged, merged_words
