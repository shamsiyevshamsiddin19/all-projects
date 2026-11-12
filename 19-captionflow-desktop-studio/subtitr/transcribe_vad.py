"""VAD va nutq oralig'iga vaqtlarni moslash qatlami."""
from __future__ import annotations

import bisect
import os
from pathlib import Path

from .core import Segment, Word

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
        if speech_seconds(media, lo, hi - lo) >= RESCAN_GAP_SPEECH:
            found.append((lo, hi))
    return sorted(found)


def speech_regions(audio_path: Path) -> list[tuple[float, float]]:
    """Silero VAD bilan nutq bor oraliqlarni qaytaradi (soniyada).

    Whisper'ning ichki `vad_filter`i sukunatni kesib tashlaydi-yu, uzun
    jimlikdan keyingi bo'laklarning vaqtini asl o'ringa qaytara olmaydi —
    subtitr nutqdan 15-20 soniya oldin chiqib qoladi. Shuning uchun modelga
    to'liq audio beriladi (vaqtlari to'g'ri bo'lsin), nutq bo'lmagan joydagi
    matn esa shu ro'yxat yordamida keyin olib tashlanadi."""
    try:
        from faster_whisper.audio import decode_audio
        from faster_whisper.vad import VadOptions, get_speech_timestamps
    except Exception:
        return []
    try:
        audio = decode_audio(str(audio_path), sampling_rate=16000)
        options = VadOptions(
            min_silence_duration_ms=int(os.getenv("WHISPER_MIN_SILENCE_MS", "500")),
            speech_pad_ms=int(os.getenv("WHISPER_SPEECH_PAD_MS", "400")),
        )
        chunks = get_speech_timestamps(audio, options, sampling_rate=16000)
        return [(c["start"] / 16000.0, c["end"] / 16000.0) for c in chunks]
    except Exception:
        return []


def clamp_to_speech(
    start: float, end: float, regions: list[tuple[float, float]]
) -> tuple[float, float] | None:
    """Bo'lak vaqtini nutq oralig'iga qisqartiradi.

    Whisper bo'lakni ko'pincha oldingi sukunatdan boshlab beradi — matn to'g'ri,
    lekin ekranda nutqdan ancha oldin chiqadi. Bunday bo'lakni o'chirmaymiz
    (aytilgan gap yo'qolmasin), faqat vaqtini nutq boshlangan joyga suramiz.
    Nutq umuman yo'q bo'lsa — None (bu matn to'qilgan)."""
    if not regions or end <= start:
        return (start, end)
    lo_hi: list[tuple[float, float]] = []
    i = max(0, bisect.bisect_right([r[0] for r in regions], start) - 1)
    while i < len(regions) and regions[i][0] < end:
        lo, hi = regions[i]
        if hi > start:
            lo_hi.append((max(lo, start), min(hi, end)))
        i += 1
    if not lo_hi:
        return None
    return lo_hi[0][0], lo_hi[-1][1]


def gate_by_speech(
    segments: list[Segment], words: list[Word], audio_path: Path
) -> tuple[list[Segment], list[Word]]:
    """Nutq bo'lmagan joydagi matnni olib tashlaydi.

    Lokal Whisper buni o'z ichida qiladi; Groq natijasi esa sukunat/musiqa
    ustida matn to'qib qo'ymasligi uchun tekshiriladi.
    DIQQAT: Musiqa, qo'shiq yoki fon musiqasi baland bo'lganda Silero VAD
    qo'shiq matnini musiqa deb o'ylab, xato tarzda o'chirib yubormasligi kerak.
    """
    if not segments:
        return segments, words
    if os.getenv("WHISPER_VAD", "1") in {"0", "false", "no"}:
        return segments, words
    regions = speech_regions(audio_path)
    if not regions:
        return segments, words

    total_vad = sum(hi - lo for lo, hi in regions)
    span_dur = max(1.0, segments[-1].end - segments[0].start)
    # Qo'shiqlar va baland musiqali videolarda VAD qamrovi juda past bo'ladi
    # (masalan 25% dan kam). Agar Whisper ko'p segmentlar topgan bo'lsa,
    # bu musiqiy nutq/qo'shiq bo'lib, VAD filtri haqiqiy matnni yo'qotadi.
    if (total_vad / span_dur) < 0.25 and len(segments) >= 5:
        return segments, words

    out_segments: list[Segment] = []
    for seg in segments:
        span = clamp_to_speech(seg.start, seg.end, regions)
        if span is None:
            # Agar segment bir necha so'zdan iborat bo'lsa yoki ishonchli bo'lsa,
            # uni VAD tufayli darhol o'chirib yubormaymiz (qo'shiq/musiqa bo'lishi mumkin)
            words_in_seg = len(seg.text.strip().split())
            if words_in_seg >= 3 or (seg.confidence is not None and seg.confidence >= 0.35):
                out_segments.append(seg)
            continue
        out_segments.append(Segment(span[0], span[1], seg.text, seg.confidence))

    # Agar VAD filtri natijasida segmentlarning yarmidan ko'pi yo'qolib ketsa,
    # demak VAD musiqada adashgan (false negative). Asl segmentlarni saqlaymiz.
    if len(segments) >= 5 and len(out_segments) < len(segments) * 0.6:
        return segments, words

    clamped_words = [w for w in words if clamp_to_speech(w.start, w.end, regions) is not None]
    return out_segments, clamped_words if len(clamped_words) >= len(words) * 0.5 else words
