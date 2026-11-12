"""Groq va lokal Whisper provider implementatsiyalari."""
from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from .core import FFMPEG, MODEL_DIR, Segment, Word, _count, _env_float, emit, model_candidates, normalize_lang_code, run, secret, whisper_confidence
from .media import probe_duration_seconds, strip_tags
from .transcribe_rescan import WindowTranscriber, rescan_swallowed_speech
from .transcribe_vad import clamp_to_speech, speech_regions


def groq_file(*args: Any, **kwargs: Any) -> Any:
    """Eski qatlam foydalanuvchilari uchun provider funksiyasi."""
    return _groq_transcribe_file(*args, **kwargs)


def _mmss(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"

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
                    # Groq `verbose_json` da `avg_logprob` qaytaradi, lekin
                    # u ilgari umuman o'qilmas edi.
                    whisper_confidence(seg),
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
                segs.append(Segment(start + seg.start, start + seg.end, text,
                                    whisper_confidence(seg)))
            for w in (getattr(seg, "words", None) or []):
                wds.append(Word(start + w.start, start + w.end, w.word))
        return segs, wds, getattr(info, "language", "") or ""
    return run_window


def transcribe_with_groq(
    audio_path: Path, language: str, source_media: Path | None = None
) -> tuple[list[Segment], list[Word], str]:
    key = secret("GROQ_API_KEY").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY topilmadi")
    # Chunk-path unit testlari transport qatlamini almashtiradi; bunday
    # holatda SDK o'rnatilgan bo'lishi shart emas. Haqiqiy provider esa
    # avvalgidek Groq SDK mavjudligini talab qiladi.
    try:
        from groq import Groq
        client: Any = Groq(api_key=key)
    except ModuleNotFoundError:
        if _groq_transcribe_file.__module__ == __name__:
            raise RuntimeError("Groq paketi o'rnatilmagan: pip install groq")
        client = object()
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
    spans: list[tuple[int, float, float]] = []
    idx, start = 0, 0.0
    while start < duration - 0.05:
        spans.append((idx, start, min(duration, start + chunk_sec)))
        idx += 1
        start += chunk_sec

    # Bitta bo'lakni kesib, Groq'ga yuboradi. Bo'laklar bir-biriga bog'liq
    # emas (har biri o'z vaqt siljishi bilan keladi), shuning uchun ularni
    # parallel yuborish mumkin. Natija INDEKS bo'yicha yig'iladi — tugash
    # tartibi muhim emas.
    # `done += 1` atomar emas — progress hisobini qulf bilan himoyalaymiz.
    progress_lock = threading.Lock()
    done = 0

    def transcribe_chunk(
        spec: tuple[int, float, float]
    ) -> tuple[int, list[Segment], list[Word], str, tuple[float, float] | None]:
        nonlocal done
        index, lo, hi = spec
        chunk_path = audio_path.parent / f"chunk_{index:03d}.ogg"
        try:
            # -ss so'rovdan oldin: tez qidirish, audio uchun aniqligi yetarli.
            proc = run(
                [
                    FFMPEG, "-y", "-ss", f"{lo:.3f}", "-t", f"{chunk_sec:.3f}",
                    "-i", str(audio_path),
                    "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "libopus", "-b:a", "12k",
                    str(chunk_path),
                ]
            )
            if proc.returncode != 0 or not chunk_path.exists() or chunk_path.stat().st_size == 0:
                emit(
                    "progress",
                    message=f"Diqqat: {index + 1}-qism audiosi kesilmadi "
                            f"({_mmss(lo)}-{_mmss(hi)}) — o'sha joy subtitrsiz qoladi",
                    progress=0.30,
                )
                return index, [], [], "", (lo, hi)
            # Bitta bo'lak tushsa ham butun kino yo'qolmasin.
            try:
                segs, wds, det = _groq_transcribe_file(
                    client, models, chunk_path, language, lo
                )
            except Exception as exc:
                emit(
                    "progress",
                    message=f"Diqqat: {index + 1}-qism o'qilmadi "
                            f"({_mmss(lo)}-{_mmss(hi)}): {exc}",
                    progress=0.30,
                )
                return index, [], [], "", (lo, hi)
        finally:
            chunk_path.unlink(missing_ok=True)
        with progress_lock:
            done += 1
            seen = done
        emit(
            "progress",
            message=f"Groq transkripsiya ({seen}/{total_chunks} qism)",
            progress=0.30,
        )
        return index, segs, wds, det, None

    # Audio yuklash matn so'rovidan og'irroq (har bo'lak ~2 MB) va Groq
    # bepul tarifi daqiqadagi audio sekundini ham cheklaydi — shuning uchun
    # oqimlar soni tarjimadagidan kamroq. 1 — eski ketma-ket xatti-harakat.
    workers = max(1, int(os.getenv("GROQ_AUDIO_WORKERS", "2")))
    if workers == 1 or len(spans) <= 1:
        results = [transcribe_chunk(spec) for spec in spans]
    else:
        with ThreadPoolExecutor(max_workers=min(workers, len(spans))) as pool:
            results = list(pool.map(transcribe_chunk, spans))

    # Indeks bo'yicha tartiblash: ustma-ust tushgan vaqtlar paydo bo'lmasin.
    results.sort(key=lambda r: r[0])
    segments_all: list[Segment] = []
    words_all: list[Word] = []
    detected = ""
    failed: list[tuple[float, float]] = []
    for _index, segs, wds, det, miss in results:
        segments_all.extend(segs)
        words_all.extend(wds)
        # Til BIRINCHI muvaffaqiyatli bo'lakdan olinadi (tugash tartibidan
        # emas) — natija har ishda bir xil bo'lsin.
        detected = detected or det
        if miss is not None:
            failed.append(miss)

    if not segments_all:
        raise RuntimeError("Groq Whisper bo'laklab transkripsiya qila olmadi")
    if failed:
        joined = ", ".join(f"{_mmss(a)}-{_mmss(b)}" for a, b in failed[:5])
        more = f" (+{len(failed) - 5} ta)" if len(failed) > 5 else ""
        emit(
            "progress",
            message=f"Diqqat: {len(failed)} qism o'qilmadi — {joined}{more}. "
                    "Shu oraliqlar subtitrsiz qoladi.",
            progress=0.31,
        )
    segments_all, words_all = rescan_swallowed_speech(
        _groq_window_transcriber(client, models),
        audio_path, language, segments_all, words_all, source_media,
    )
    return segments_all, words_all, detected


def transcribe_with_faster_whisper(
    audio_path: Path, language: str, source_media: Path | None = None
) -> tuple[list[Segment], list[Word], str]:
    from faster_whisper import WhisperModel

    model_name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "auto")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    # Model ATAYIN keshlanmaydi (modul darajasidagi global emas).
    #
    # Shu funksiya bir jarayonda BIR MARTA chaqiriladi (`get_transcription`),
    # qayta o'qish esa ayni shu `model` obyektini ishlatadi — ya'ni yuklash
    # allaqachon bir martalik. O'lchangan: 2.16s sovuq, ~0.95s issiq.
    #
    # Global keshda ushlab turish FOYDA bermaydi, zarar beradi: model yuzlab
    # megabayt xotirani egallab, transkripsiya tugagandan keyin ham —
    # render bosqichi davomida — bo'shamay turadi. Navbat (batch) rejimida
    # ham yordam bermaydi, chunki ilova HAR VIDEO uchun yangi jarayon
    # ishga tushiradi (jarayonning o'zi 0.07s).
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
            segments.append(Segment(min(start, end), max(start, end), text,
                                    whisper_confidence(seg)))
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
