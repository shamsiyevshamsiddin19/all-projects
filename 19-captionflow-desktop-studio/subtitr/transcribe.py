"""Nutqni matnga aylantirish: Groq Whisper, lokal model, yutilgan nutqni tiklash."""
from __future__ import annotations

import bisect
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from .core import FFMPEG, MODEL_DIR, Segment, Word, _count, _env_float, emit, model_candidates, normalize_lang_code, run, words_from_segments
from .media import extract_audio, extract_embedded_subtitle, find_sidecar_subtitle, parse_srt, parse_vtt, probe_duration_seconds, strip_tags
from .clean import is_hallucination


def value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _groq_transcribe_file(
    client: Any,
    models: list[str],
    audio_path: Path,
    language: str,
    offset: float,
) -> tuple[list[Segment], list[Word], str]:
    """Transcribe a single audio file with Groq, shifting times by `offset`."""
    data = audio_path.read_bytes()
    resp = None
    last_error: Exception | None = None
    _count("whisper")
    for model in models:
        kwargs: dict[str, Any] = {"model": model, "response_format": "verbose_json"}
        if language and language != "auto":
            kwargs["language"] = language
        try:
            try:
                resp = client.audio.transcriptions.create(
                    file=(audio_path.name, data),
                    timestamp_granularities=["word", "segment"],
                    **kwargs,
                )
            except TypeError:
                resp = client.audio.transcriptions.create(file=(audio_path.name, data), **kwargs)
            break
        except Exception as exc:
            last_error = exc
            continue
    if resp is None:
        raise RuntimeError(f"Groq Whisper ishlamadi: {last_error}")

    detected = str(value(resp, "language", "") or "").lower()
    segments: list[Segment] = []
    for seg in value(resp, "segments", []) or []:
        text = strip_tags(str(value(seg, "text", "") or ""))
        if text:
            segments.append(
                Segment(
                    offset + float(value(seg, "start", 0.0) or 0.0),
                    offset + float(value(seg, "end", 0.0) or 0.0),
                    text,
                )
            )
    words: list[Word] = []
    for item in value(resp, "words", []) or []:
        text = strip_tags(str(value(item, "word", "") or ""))
        if text:
            words.append(
                Word(
                    offset + float(value(item, "start", 0.0) or 0.0),
                    offset + float(value(item, "end", 0.0) or 0.0),
                    text,
                )
            )
    return segments, words, detected


# --- Musiqa ostida "yutib yuborilgan" nutqni qayta o'qish -------------------
# Whisper audioni 30 soniyalik oynalarda tinglaydi. Oynaning katta qismi musiqa
# bo'lsa, model butun oynani BITTA qisqa soxta qatorga siqib yuboradi
# ("Девушки отдыхают", "Музыка") va oynadagi haqiqiy nutq butunlay yo'qoladi —
# subtitrda bo'sh joy qoladi. STOCK_PHRASE_RE soxta qatorni o'chiradi, lekin
# yo'qolgan nutqni qaytarmaydi.
#
# Bunday joyni matn ZICHLIGI ochib beradi: haqiqiy nutq ~10-20 belgi/sek, soxta
# qator esa 30 soniyaga 16 belgi (~0.5 belgi/sek). O'sha oraliqni qisqa —
# musiqa bilan to'lib ketmaydigan — oynalarda qayta o'qiymiz.
RESCAN_MIN_DUR = 10.0      # shubha uchun eng kam segment davomiyligi (sek)
RESCAN_MAX_CPS = 4.0       # belgi/sek — bundan past bo'lsa shubhali
RESCAN_WINDOW = 12.0       # qayta o'qish oynasi (sek)
RESCAN_OVERLAP = 6.0       # oynalar ustma-ustligi — jumla chegarada kesilmasin
RESCAN_PAD = 3.0           # oraliq chetidan tashqariga qo'shimcha
RESCAN_MAX_TOTAL = 180.0   # jami qayta o'qiladigan vaqt chegarasi (xarajat)
RESCAN_MAX_WINDOWS = 30    # qo'shimcha so'rovlar soni chegarasi
RESCAN_EDGE = 0.6          # segment oyna boshiga shuncha yaqin = jumla kesilgan
RESCAN_SHIFTS = (2.0, 4.0)  # kesilgan joyni shuncha oldinroqdan qayta o'qiymiz
RESCAN_MAX_RETRY = 8       # surilgan qo'shimcha oynalar soni chegarasi
# Groq ba'zan butun bir parchani umuman qaytarmaydi — segmentlar orasida
# teshik qoladi va subtitr ekranda yo'qolib turadi. Quyidagilar o'sha
# teshiklarni topish uchun.
RESCAN_GAP_MIN = 3.0       # shu soniyadan uzun bo'shliq — nomzod
RESCAN_GAP_SPEECH = 1.5    # bo'shliqda shuncha soniya nutq bo'lsa qayta o'qiladi
RESCAN_GAP_MAX_CHECKS = 25 # nechta bo'shliqni tekshirishga arziydi


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
        if speech_seconds(media, lo, hi - lo) >= RESCAN_GAP_SPEECH:
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
    ranges = ranges_within_budget(
        suspect_ranges(segments)
        + swallowed_gap_ranges(cut_from, segments, probe_duration_seconds(cut_from))
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
            segs, wds = _rescan_one(
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
    # ikkita subtitr bir vaqtda chiqmasin
    for cur, nxt in zip(merged, merged[1:]):
        if cur.end > nxt.start:
            cur.end = max(cur.start + 0.2, nxt.start)
    merged_words = sorted(
        [w for w in words if outside(w.start, w.end)] + kept_new_words,
        key=lambda w: w.start,
    )
    return merged, merged_words


def _groq_window_transcriber(client: Any, models: list[str]) -> "WindowTranscriber":
    def run_window(part: Path, language: str, start: float):
        return _groq_transcribe_file(client, models, part, language, start)
    return run_window


def _local_window_transcriber(model: Any, fallback_lang: str) -> "WindowTranscriber":
    """Lokal faster-whisper modelini qayta o'qish uchun o'raydi.

    Model allaqachon xotirada — qayta yuklanmaydi, shuning uchun oyna
    narxi faqat protsessor vaqti (pul emas)."""
    def run_window(part: Path, language: str, start: float):
        lang = normalize_lang_code(language) or normalize_lang_code(fallback_lang)
        kwargs: dict[str, Any] = {"word_timestamps": True, "vad_filter": False,
                                  "condition_on_previous_text": False}
        if lang:
            kwargs["language"] = lang
        seg_iter, info = model.transcribe(str(part), **kwargs)
        segs: list[Segment] = []
        wds: list[Word] = []
        for seg in seg_iter:
            text = (seg.text or "").strip()
            if text:
                segs.append(Segment(start + seg.start, start + seg.end, text))
            for w in (getattr(seg, "words", None) or []):
                wds.append(Word(start + w.start, start + w.end, w.word))
        return segs, wds, getattr(info, "language", "") or ""
    return run_window


def transcribe_with_groq(
    audio_path: Path, language: str, source_media: Path | None = None
) -> tuple[list[Segment], list[Word], str]:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY topilmadi")
    from groq import Groq

    client = Groq(api_key=key)
    models = model_candidates(
        "GROQ_WHISPER_MODEL",
        "whisper-large-v3",
        "GROQ_WHISPER_FALLBACK_MODELS",
        ["whisper-large-v3-turbo"],
    )

    # Qisqa audio — bitta so'rovda. Uzun kino (Groq hajm limitiga yaqin yoki
    # undan katta) bo'laklarga bo'linadi va har bo'lak vaqti surib qo'shiladi.
    size = audio_path.stat().st_size
    size_limit = int(os.getenv("GROQ_AUDIO_CHUNK_BYTES", str(20 * 1024 * 1024)))
    if size <= size_limit:
        segs, wds, det = _groq_transcribe_file(client, models, audio_path, language, 0.0)
        segs, wds = rescan_swallowed_speech(
            _groq_window_transcriber(client, models),
            audio_path, language, segs, wds, source_media,
        )
        return segs, wds, det

    duration = probe_duration_seconds(audio_path)
    chunk_sec = max(60.0, float(os.getenv("GROQ_CHUNK_SECONDS", "1200")))  # 20 daqiqa
    if duration <= 0:
        duration = chunk_sec  # noma'lum — hech bo'lmasa bitta bo'lak

    total_chunks = int((duration + chunk_sec - 1) // chunk_sec)
    segments_all: list[Segment] = []
    words_all: list[Word] = []
    detected = ""
    idx = 0
    start = 0.0
    while start < duration - 0.05:
        chunk_path = audio_path.parent / f"chunk_{idx:03d}.ogg"
        # -ss so'rovdan oldin: tez qidirish, audio uchun aniqligi yetarli.
        proc = run(
            [
                FFMPEG, "-y", "-ss", f"{start:.3f}", "-t", f"{chunk_sec:.3f}",
                "-i", str(audio_path),
                "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "libopus", "-b:a", "12k",
                str(chunk_path),
            ]
        )
        if proc.returncode == 0 and chunk_path.exists() and chunk_path.stat().st_size > 0:
            emit(
                "progress",
                message=f"Groq transkripsiya (qism {idx + 1}/{total_chunks})",
                progress=0.30,
            )
            segs, wds, det = _groq_transcribe_file(client, models, chunk_path, language, start)
            segments_all.extend(segs)
            words_all.extend(wds)
            detected = detected or det
            chunk_path.unlink(missing_ok=True)
        idx += 1
        start += chunk_sec

    if not segments_all:
        raise RuntimeError("Groq Whisper bo'laklab transkripsiya qila olmadi")
    segments_all, words_all = rescan_swallowed_speech(
        _groq_window_transcriber(client, models),
        audio_path, language, segments_all, words_all, source_media,
    )
    return segments_all, words_all, detected


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

    Lokal Whisper buni o'z ichida qiladi; Groq natijasi esa hech qanday
    tekshiruvdan o'tmasdi — u ham sukunat/musiqa ustida matn to'qib qo'yadi."""
    if os.getenv("WHISPER_VAD", "1") in {"0", "false", "no"}:
        return segments, words
    regions = speech_regions(audio_path)
    if not regions:
        return segments, words
    out_segments: list[Segment] = []
    for seg in segments:
        span = clamp_to_speech(seg.start, seg.end, regions)
        if span is None:
            continue  # nutq yo'q joyda paydo bo'lgan matn — to'qilgan
        out_segments.append(Segment(span[0], span[1], seg.text))
    out_words = [w for w in words if clamp_to_speech(w.start, w.end, regions) is not None]
    return out_segments, out_words


def transcribe_with_faster_whisper(
    audio_path: Path, language: str, source_media: Path | None = None
) -> tuple[list[Segment], list[Word], str]:
    from faster_whisper import WhisperModel

    model_name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "auto")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    model = WhisperModel(model_name, device=device, compute_type=compute_type, download_root=str(MODEL_DIR))
    # Whisper sukut bo'yicha sukunatni ham "eshitadi" va oldingi matnga qarab
    # gapni o'zi to'qib davom ettiradi. Quyidagilar shuni to'xtatadi:
    #   vad_filter                 — nutq bo'lmagan qismlarni modelga bermaydi
    #   condition_on_previous_text — oldingi matndan takrorlanuvchi tsikl chiqmaydi
    #   hallucination_silence_threshold — uzoq sukutda paydo bo'lgan matnni tashlaydi
    kwargs: dict[str, Any] = {
        "word_timestamps": True,
        # Ichki VAD o'chirilgan — vaqtlar buzilmasin. Nutqsiz joydagi matn
        # `speech_regions()` yordamida quyida olib tashlanadi.
        "vad_filter": False,
        "condition_on_previous_text": False,
        "no_speech_threshold": _env_float("WHISPER_NO_SPEECH", 0.6),
        "compression_ratio_threshold": _env_float("WHISPER_COMPRESSION_RATIO", 2.4),
        "log_prob_threshold": _env_float("WHISPER_LOGPROB", -1.0),
        "hallucination_silence_threshold": _env_float("WHISPER_HALLUCINATION_SILENCE", 2.0),
    }
    if language and language != "auto":
        kwargs["language"] = language
    seg_iter, info = model.transcribe(str(audio_path), **kwargs)
    # Til past ishonch bilan aniqlansa, model taxmin qilyapti — natija ko'pincha
    # aslida aytilmagan matn bo'ladi. Foydalanuvchini ogohlantiramiz.
    prob = float(getattr(info, "language_probability", 0.0) or 0.0)
    if (not language or language == "auto") and 0 < prob < _env_float("WHISPER_MIN_LANG_PROB", 0.5):
        emit(
            "progress",
            message=f"Diqqat: til aniq emas ({getattr(info, 'language', '?')} {prob:.0%}) — "
                    "video tilini qo'lda tanlang",
            progress=0.32,
        )
    # VAD yoqilganda faster-whisper (1.2.x) ba'zan bo'lakning birinchi so'ziga
    # sukunatning boshini (0.00) yozib yuboradi: subtitr nutqdan 10-15 soniya
    # oldin chiqib, ekranda osilib qoladi. Bitta so'z bir soniyadan uzun
    # cho'zilmaydi — shunday "cho'zilgan" so'zni oxiriga tortamiz va bo'lak
    # vaqtini so'z vaqtlaridan qayta hisoblaymiz.
    max_word_dur = _env_float("WHISPER_MAX_WORD_DUR", 1.0)
    max_word_gap = _env_float("WHISPER_MAX_WORD_GAP", 2.0)
    # Uchinchi himoya qatlami (VAD va tayyor ibora ro'yxatidan keyin): model
    # "bu yerda nutq yo'q" deb baholagan, lekin baribir matn yozgan bo'laklar.
    # O'lchov: haqiqiy nutqda bu ko'rsatkich 0.87 gacha chiqdi (musiqa fonidagi
    # multfilm), to'qilgan matnlarda 0.95-0.98. Chegara pastroq bo'lsa haqiqiy
    # nutq o'chib ketadi.
    max_no_speech = _env_float("WHISPER_MAX_NO_SPEECH", 0.93)
    use_vad = os.getenv("WHISPER_VAD", "1") not in {"0", "false", "no"}
    regions = speech_regions(audio_path) if use_vad else []

    def repair_leading(items: list[Word]) -> list[Word]:
        """Bo'lak boshidagi noto'g'ri vaqtli so'zlarni keyingisiga tortadi.

        Xato ko'rinishi: birinchi so'z 0.00 da, ikkinchisi 16.5 da — ya'ni
        birinchi so'z sukunat boshiga tashlab yuborilgan. Uni o'chirmaymiz
        (aytilgan so'z), faqat vaqtini haqiqiy nutqqa yaqinlashtiramiz."""
        if len(items) < 2:
            return items
        k = 0
        while k + 1 < len(items) and items[k + 1].start - items[k].end > max_word_gap:
            k += 1
        if k == 0:
            return items
        out = list(items)
        for i in range(k - 1, -1, -1):
            end = out[i + 1].start
            dur = min(max_word_dur, max(0.05, out[i].end - out[i].start))
            out[i] = Word(max(0.0, end - dur), end, out[i].word)
        return out

    segments: list[Segment] = []
    words: list[Word] = []
    for seg in seg_iter:
        if float(getattr(seg, "no_speech_prob", 0.0) or 0.0) > max_no_speech:
            continue
        seg_start, seg_end = float(seg.start), float(seg.end)
        if regions:
            span = clamp_to_speech(seg_start, seg_end, regions)
            if span is None:
                continue  # nutq bo'lmagan joyda paydo bo'lgan matn — to'qilgan
            seg_start, seg_end = span
        text = strip_tags(seg.text or "")
        seg_words: list[Word] = []
        for w in seg.words or []:
            word = strip_tags(w.word or "")
            if not word:
                continue
            start, end = float(w.start), float(w.end)
            if end - start > max_word_dur:
                start = end - max_word_dur
            seg_words.append(Word(start, end, word))
        seg_words = repair_leading(seg_words)
        if text:
            # So'z vaqtlari bo'lsa — aniqrog'i shular, lekin ular ham nutq
            # oralig'idan chiqib ketmasligi kerak.
            start = seg_words[0].start if seg_words else seg_start
            end = seg_words[-1].end if seg_words else seg_end
            start = min(max(start, seg_start), seg_end)
            end = max(min(end, seg_end), seg_start)
            segments.append(Segment(min(start, end), max(start, end), text))
        words.extend(seg_words)
    if not segments:
        # Barcha bo'laklar ishonchsizligi uchun chiqarib tashlandi — bu "model
        # bu tilni tanimadi" degani. To'qib chiqarilgan matn berishdan ko'ra
        # nima qilish kerakligini aytamiz.
        raise RuntimeError(
            f"lokal model nutqni ishonchli tanimadi (til: {getattr(info, 'language', '?')}). "
            "Video tilini qo'lda tanlang yoki Groq kalitini kiriting (whisper-large-v3)"
        )
    detected = getattr(info, "language", "") or ""
    # Lokal model ham nutqni yutib yuborishi mumkin (ayniqsa musiqa ustida).
    # Groq yo'lidagi bilan bir xil tiklash: teshiklar topiladi, lokal VAD
    # bilan tekshiriladi va faqat nutq bor joy qayta o'qiladi. Bu yerda
    # narx — protsessor vaqti, pul emas.
    segments, words = rescan_swallowed_speech(
        _local_window_transcriber(model, detected or language),
        audio_path, detected or language, segments, words, source_media,
    )
    return segments, words, detected


def transcribe_with_whisper_cli(audio_path: Path, tmp_dir: Path, language: str) -> tuple[list[Segment], list[Word], str]:
    exe = shutil.which("whisper")
    if not exe:
        raise RuntimeError("whisper CLI topilmadi")
    model = os.getenv("WHISPER_MODEL", "small")
    cmd = [
        exe, str(audio_path),
        "--model", model,
        "--output_format", "srt",
        "--output_dir", str(tmp_dir),
    ]
    if language and language != "auto":
        cmd += ["--language", language]
    proc = run(cmd)
    if proc.returncode != 0:
        raise RuntimeError("whisper CLI xato: " + (proc.stderr[-700:] or "noma'lum"))
    srt = tmp_dir / (audio_path.stem + ".srt")
    segments = parse_srt(srt)
    return segments, words_from_segments(segments), language if language != "auto" else ""


def get_transcription(video: Path, tmp_dir: Path, source_lang: str) -> tuple[list[Segment], list[Word], str, str]:
    sidecar = find_sidecar_subtitle(video)
    if sidecar:
        emit("progress", message=f"SRT topildi: {sidecar.name}", progress=0.12)
        segments = parse_vtt(sidecar) if sidecar.suffix.lower() == ".vtt" else parse_srt(sidecar)
        return segments, words_from_segments(segments), source_lang if source_lang != "auto" else "", "sidecar_srt"

    embedded = extract_embedded_subtitle(video, tmp_dir)
    if embedded:
        emit("progress", message="Ichki subtitr ajratildi", progress=0.16)
        segments = parse_srt(embedded)
        return segments, words_from_segments(segments), source_lang if source_lang != "auto" else "", "embedded_srt"

    # Audio ikki xil sifatda kerak bo'ladi: Groq'ga siqilgani (yuklash tez),
    # lokal Whisper'ga siqilmagani (aniqlik). Faqat kerak bo'lganda ajratamiz.
    cache: dict[str, Path] = {}

    def audio_for(lossless: bool) -> Path:
        key = "wav" if lossless else "opus"
        if key not in cache:
            path = tmp_dir / ("audio.wav" if lossless else "audio.webm")
            emit(
                "progress",
                message="Audio ajratilmoqda" if lossless else "Audio ajratilmoqda (yuqori siqilishda)",
                progress=0.18,
            )
            extract_audio(video, path, lossless=lossless)
            cache[key] = path
        return cache[key]

    errors: list[str] = []
    if os.getenv("GROQ_API_KEY", "").strip():
        try:
            emit("progress", message="Groq Whisper transkripsiya qilmoqda", progress=0.30)
            segments, words, detected = transcribe_with_groq(
                audio_for(False), source_lang, video
            )
            segments, words = gate_by_speech(segments, words, audio_for(False))
            if not segments:
                raise RuntimeError("nutq topilmadi")
            return segments, words or words_from_segments(segments), detected, "groq"
        except Exception as exc:
            errors.append(f"Groq: {exc}")

    try:
        emit("progress", message="Lokal faster-whisper tekshirilmoqda", progress=0.30)
        segments, words, detected = transcribe_with_faster_whisper(
            audio_for(True), source_lang, video
        )
        return segments, words or words_from_segments(segments), detected, "faster_whisper"
    except Exception as exc:
        errors.append(f"faster-whisper: {exc}")

    try:
        emit("progress", message="Lokal whisper CLI tekshirilmoqda", progress=0.30)
        segments, words, detected = transcribe_with_whisper_cli(audio_for(True), tmp_dir, source_lang)
        return segments, words, detected, "whisper_cli"
    except Exception as exc:
        errors.append(f"whisper CLI: {exc}")

    detail = " | ".join(errors[-3:])
    raise RuntimeError(
        "Subtitr topilmadi va transkripsiya ishlamadi. Video yoniga .srt qo'ying "
        "yoki GROQ_API_KEY / faster-whisper / whisper CLI sozlang. " + detail
    )
