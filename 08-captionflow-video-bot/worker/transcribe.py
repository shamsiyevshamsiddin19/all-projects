"""Groq Whisper orqali audio -> matn (segmentlar bilan).

Lokal whisper o'rniga Groq API ishlatamiz: tez va aniqroq (large-v3).
Bu funksiya sinxron (CPU/tarmoq bilan ishlaydi) — pipeline uni
asyncio.to_thread ichida chaqiradi, shunda bot bloklanmaydi.

Uzun audio (TRANSCRIBE_CHUNK_SECONDS dan katta) bo'laklarga bo'linib
PARALLEL transkripsiya qilinadi — 1-2 soatlik kinoda ancha tezroq va Groq
fayl-hajm/limitiga urilib qolmaydi. Bo'lak vaqtlari ofset bilan qo'shiladi.

Musiqa/shovqin ustidagi nutqni Whisper ba'zan butunlay "yutib" yuboradi —
o'sha oraliqlar aniqlanib, qisqa oynalarda qayta o'qiladi (pastdagi
"Yutib yuborilgan nutqni qayta o'qish" bo'limiga qarang).

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
from worker.clean import is_hallucination
from worker.ffmpeg_utils import cut_audio, probe_duration, split_audio

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


# --- "Yutib yuborilgan" nutqni qayta o'qish ---------------------------------
# Whisper audioni 30 soniyalik oynalarda tinglaydi. Oynaning katta qismi musiqa
# yoki shovqin bo'lsa, model butun oynani BITTA qisqa soxta qatorga siqib
# yuboradi ("Девушки отдыхают", "Субтитры создавал DimaTorzok", "Музыка") va
# o'sha oynadagi haqiqiy nutq butunlay yo'qoladi — subtitrda bo'sh joy qoladi.
#
# Bunday segmentni matn ZICHLIGI ochib beradi: haqiqiy nutq ~10-20 belgi/sek,
# soxta qator esa 30 soniyaga 16 belgi (~0.5 belgi/sek). Shubhali oraliqni
# qisqa (musiqa bilan "to'lib ketmaydigan") oynalarda qayta o'qiymiz.
_RESCAN_MIN_DUR = 10.0     # shubha uchun eng kam segment davomiyligi (sek)
_RESCAN_MAX_CPS = 4.0      # belgi/sek — bundan past bo'lsa shubhali
_RESCAN_WINDOW = 12.0      # qayta o'qish oynasi (sek) — qisqa oyna musiqa
                           # ustidan nutqni yaxshiroq ilib oladi
_RESCAN_OVERLAP = 6.0      # oynalar ustma-ustligi — jumla chegarada kesilmasin
_RESCAN_PAD = 3.0          # oraliq chetidan tashqariga qo'shimcha (jumla
                           # chegarada yarim qolmasin)
_RESCAN_MAX_TOTAL = 180.0  # jami qayta o'qiladigan vaqt chegarasi (xarajat)
_RESCAN_MAX_WINDOWS = 30   # qo'shimcha so'rovlar soni chegarasi — Groq'ning
                           # daqiqalik so'rov limitini yeb qo'ymasin
_RESCAN_EDGE = 0.6         # segment oyna boshiga shuncha yaqin bo'lsa —
                           # jumla kesilgan deb hisoblaymiz
_RESCAN_SHIFTS = (2.0, 4.0)  # kesilgan joyni shuncha oldinroqdan qayta o'qiymiz
_RESCAN_MAX_RETRY = 8      # qo'shimcha (surilgan) oynalar soni chegarasi


def _density(seg: dict) -> float:
    """Segment matn zichligi (belgi/sek). Haqiqiy nutq ~10-20, soxta qator <1."""
    dur = max(0.01, float(seg["end"]) - float(seg["start"]))
    return len((seg.get("text") or "").strip()) / dur


def _suspect_ranges(segments: list[dict]) -> list[tuple[float, float]]:
    """Matn zichligi juda past segment oraliqlarini qaytaradi (qo'shni
    shubhalilar bitta oraliqqa birlashtiriladi)."""
    ranges: list[tuple[float, float]] = []
    for seg in segments:
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        if end - start < _RESCAN_MIN_DUR or _density(seg) > _RESCAN_MAX_CPS:
            continue
        if ranges and start - ranges[-1][1] < 1.0:
            ranges[-1] = (ranges[-1][0], end)
        else:
            ranges.append((start, end))

    # Xarajatni cheklaymiz: eng uzun (eng shubhali) oraliqlardan boshlab olamiz
    total = 0.0
    picked: list[tuple[float, float]] = []
    for rng in sorted(ranges, key=lambda r: r[1] - r[0], reverse=True):
        span = rng[1] - rng[0]
        if total + span > _RESCAN_MAX_TOTAL:
            continue
        picked.append(rng)
        total += span
    return sorted(picked)


def _windows(rs: float, re_: float) -> list[tuple[float, float]]:
    """Oraliqni USTMA-UST oynalarga bo'ladi: bitta oynaning chetida kesilgan
    jumla qo'shni oynaning o'rtasiga tushadi va u yerda to'liq eshitiladi."""
    step = max(1.0, _RESCAN_WINDOW - _RESCAN_OVERLAP)
    out: list[tuple[float, float]] = []
    pos = rs
    while pos < re_ - 0.5:
        out.append((pos, min(_RESCAN_WINDOW, re_ - pos)))
        pos += step
    return out


def _rescan_window(
    audio_path: str, start: float, dur: float, base_kwargs: dict
) -> tuple[list[dict], list[dict]]:
    """Bitta oynani kesib olib qayta transkripsiya qiladi."""
    base, ext = os.path.splitext(audio_path)
    out = f"{base}.rescan{int(start * 1000)}{ext}"
    try:
        cut_audio(audio_path, start, dur, out)
        with open(out, "rb") as f:
            data = f.read()
    except Exception as exc:
        logger.warning("Oynani kesib bo'lmadi (%.1fs): %s", start, exc)
        return [], []

    try:
        resp = _transcribe_bytes(os.path.basename(out), data, base_kwargs)
        segs, words, _ = _parse_response(resp, start)
    except Exception as exc:  # bitta oyna tushsa ham butun ish to'xtamasin
        logger.warning("Qayta o'qish muvaffaqiyatsiz (%.1fs): %s", start, exc)
        return [], []
    finally:
        try:
            os.remove(out)
        except OSError:
            pass

    # Soxta qator (musiqa/subtitr-krediti) nomzodlikka ham tushmasin — aks holda
    # u haqiqiy jumlaning o'rnini egallab qolishi mumkin
    segs = [x for x in segs if not is_hallucination(x.get("text", ""))]
    # Qaysi oynadan kelgani — so'zni segmentiga bog'lash va chegarada kesilganini
    # aniqlash uchun kerak
    for item in segs:
        item["_win"] = start
    for item in words:
        item["_win"] = start
    return segs, words


def _pick_best(segments: list[dict]) -> list[dict]:
    """Ustma-ust oynalardan kelgan nomzodlardan eng "to'liqlarini" tanlaydi.

    Matni eng UZUN nomzoddan boshlab olamiz; vaqt bo'yicha unga jiddiy tegib
    turgan qolganlari tashlanadi. Shu tariqa oyna chetida kesilgan yarim jumla
    ("Май ещё долго будет") o'rniga to'liq varianti ("Гена, зима ещё долго
    будет?") saqlanadi."""
    def rank(seg: dict) -> tuple[int, float]:
        return (len((seg.get("text") or "").strip()), _density(seg))

    kept: list[dict] = []
    for seg in sorted(segments, key=rank, reverse=True):
        dur = max(0.01, seg["end"] - seg["start"])
        clash = False
        for prev in kept:
            overlap = min(prev["end"], seg["end"]) - max(prev["start"], seg["start"])
            if overlap > 0.5 * min(dur, prev["end"] - prev["start"]):
                clash = True
                break
        if not clash:
            kept.append(seg)
    return sorted(kept, key=lambda s: s["start"])


def _rescan_gaps(
    audio_path: str,
    segments: list[dict],
    words: list[dict],
    base_kwargs: dict,
) -> tuple[list[dict], list[dict]]:
    """Shubhali oraliqlarni qisqa oynalarda qayta o'qib, natijani almashtiradi."""
    ranges = _suspect_ranges(segments)
    if not ranges:
        return segments, words

    jobs = [
        w for rs, re_ in ranges
        for w in _windows(max(0.0, rs - _RESCAN_PAD), re_ + _RESCAN_PAD)
    ][:_RESCAN_MAX_WINDOWS]
    logger.info(
        "Shubhali (nutq yutilgan) %d oraliq — %d oynada qayta o'qilmoqda",
        len(ranges), len(jobs),
    )

    new_segments: list[dict] = []
    new_words: list[dict] = []

    def run(batch: list[tuple[float, float]]) -> None:
        if not batch:
            return
        workers = max(1, min(settings.transcribe_parallel, len(batch)))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [
                ex.submit(_rescan_window, audio_path, st, dur, base_kwargs)
                for st, dur in batch
            ]
            for fut in futures:
                segs, wds = fut.result()
                new_segments.extend(segs)
                new_words.extend(wds)

    run(jobs)

    # 2-bosqich: oynaning ENG BOSHIDA turgan segment — jumla chegarada kesilgan
    # degani (masalan "Май ещё долго будет" — aslida "Гена, зима ещё
    # долго будет?"). Whisper oynani musiqadan emas, nutqdan boshlaganda to'g'ri
    # eshitadi, shuning uchun o'sha joyni bir-ikki soniya oldinroqdan qayta
    # o'qiymiz va to'liqroq variantini olamiz.
    done = {round(st, 2) for st, _dur in jobs}
    retries: list[tuple[float, float]] = []
    for seg in new_segments:
        win_start = seg["_win"]
        if seg["start"] - win_start > _RESCAN_EDGE:
            continue
        for shift in _RESCAN_SHIFTS:
            st = max(0.0, win_start - shift)
            if round(st, 2) in done or st >= win_start:
                continue
            done.add(round(st, 2))
            retries.append((st, _RESCAN_WINDOW))
    if retries:
        retries = sorted(retries)[:_RESCAN_MAX_RETRY]
        logger.info("Chegarada kesilgan %d joy oldinroqdan qayta o'qilmoqda", len(retries))
        run(retries)

    if not new_segments:
        return segments, words

    # Pad tufayli oraliqdan tashqariga chiqqan segmentlar kerak emas — u yerni
    # asosiy transkripsiya allaqachon to'g'ri o'qigan
    new_segments = [
        s for s in new_segments
        if any(rs <= (s["start"] + s["end"]) / 2.0 <= re_ for rs, re_ in ranges)
    ]
    new_segments = _pick_best(new_segments)
    # Qisqa oynada ham zichligi past qolgan segment — bu haqiqiy nutq emas,
    # musiqa ustidagi soxta qator. Uni saqlagandan ko'ra tashlagan ma'qul.
    new_segments = [
        x for x in new_segments
        if x["end"] - x["start"] < _RESCAN_MIN_DUR or _density(x) > _RESCAN_MAX_CPS
    ]
    # So'z faqat O'Z oynasidan saqlangan segment ichida qolsa oladi
    spans = {(s["_win"], s["start"], s["end"]) for s in new_segments}
    new_words = [
        w for w in new_words
        if any(
            w["_win"] == win and a - 0.05 <= w["start"] <= b + 0.05
            for win, a, b in spans
        )
    ]
    for item in new_segments + new_words:
        item.pop("_win", None)

    # Faqat HAQIQATAN yangi matn topilgan oraliqlar almashtiriladi: qayta
    # o'qish bo'sh qaytgan oraliqda eski matn joyida qolsin (yo'qotmaylik).
    replaced = [
        (rs, re_) for rs, re_ in ranges
        if any(rs <= (x["start"] + x["end"]) / 2.0 <= re_ for x in new_segments)
    ]

    def _outside(start: float, end: float) -> bool:
        mid = (start + end) / 2.0
        return not any(rs <= mid <= re_ for rs, re_ in replaced)

    kept = [
        s for s in segments
        if _outside(float(s.get("start", 0.0)), float(s.get("end", 0.0)))
    ]
    kept_words = [
        w for w in words
        if _outside(float(w.get("start", 0.0)), float(w.get("end", w.get("start", 0.0))))
    ]

    merged = sorted(kept + new_segments, key=lambda s: s["start"])
    # Qayta o'qilgan oyna qo'shni segmentga tegib ketishi mumkin — ekranda
    # ikkita subtitr bir vaqtda chiqmasin
    for cur, nxt in zip(merged, merged[1:]):
        if cur["end"] > nxt["start"]:
            cur["end"] = max(cur["start"] + 0.2, nxt["start"])
    merged_words = sorted(kept_words + new_words, key=lambda w: w["start"])
    return merged, merged_words


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
        segs, words = _rescan_gaps(audio_path, segs, words, base_kwargs)
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
        segs, words = _rescan_gaps(audio_path, segs, words, base_kwargs)
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
    all_segments, all_words = _rescan_gaps(
        audio_path, all_segments, all_words, base_kwargs
    )
    if not forced:
        detected = _refine_language(detected, all_segments)
    return all_segments, all_words, detected
