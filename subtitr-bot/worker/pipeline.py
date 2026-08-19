"""Video -> subtitrli video to'liq zanjiri (moslashuvchan cue tizimi).

Rejimlar: original / translate / dual / srt (arxitektura 3.1).
Subtitr bloklar video o'lchamiga moslashadi va o'qish tezligiga qarab
vaqtlanadi (worker/cues.py). Og'ir ishlar asyncio.to_thread da.
"""
from __future__ import annotations

import asyncio
import glob
import os
from typing import Awaitable, Callable

from config import settings
from worker import docgen, substyle
from worker.clean import clean_segments
from worker.correct import correct_segments
from worker.cues import build_cues, compute_layout
from worker.ffmpeg_utils import (
    burn_subtitles,
    extract_audio,
    extract_audio_hq,
    probe_resolution,
)
from worker.subtitles import (
    cues_to_ass,
    cues_to_ass_dual,
    cues_to_ass_dual_vocab,
    cues_to_srt,
)
from worker.titler import make_title
from worker.transcribe import transcribe
from worker.translate import translate_texts
from worker.vocab import build_vocab_map, build_vocabulary

# Bot username (main.py bot jarayonida o'rnatadi) — PDF suvbelgisi uchun.
# Celery worker'da main.py ishlamaydi, shuning uchun .env (settings.bot_brand)ga tushadi.
BOT_BRAND = ""


def _brand() -> str:
    return BOT_BRAND or settings.bot_brand or ""


def _write_name(out_path: str, slug: str) -> None:
    """Natija faylga mos nomни (slug) yondosh faylga yozadi — worker shu nom
    bilan Telegramga yuboradi (video nomiga mos, tushunarsiz raqamlar emas)."""
    try:
        with open(out_path + ".name", "w", encoding="utf-8") as f:
            f.write((slug or "").strip())
    except OSError:
        pass

_LANG_CODE = {"uzbek": "uz", "russian": "ru", "english": "en"}


def _norm_lang(value: str) -> str:
    value = (value or "").lower()
    return _LANG_CODE.get(value, value)


ProgressFn = Callable[[str], Awaitable[None]]


def job_paths(job_id: str) -> dict[str, str]:
    work = settings.work_dir
    return {
        "video": os.path.join(work, f"{job_id}.mp4"),
        "audio": os.path.join(work, f"{job_id}.mp3"),
        "ass": os.path.join(work, f"{job_id}.ass"),
        "srt": os.path.join(work, f"{job_id}.srt"),
        "out": os.path.join(work, f"{job_id}_out.mp4"),
        "txt": os.path.join(work, f"{job_id}.txt"),
        "pdf": os.path.join(work, f"{job_id}.pdf"),
        "title": os.path.join(work, f"{job_id}.title"),
        "audio_out": os.path.join(work, f"{job_id}_audio.mp3"),
    }


def cleanup(job_id: str) -> None:
    for path in job_paths(job_id).values():
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


async def process_video(
    in_path: str,
    job_id: str,
    progress: ProgressFn,
    *,
    mode: str,
    source_lang: str | None,
    target_lang: str | None,
    style: dict | None = None,
    transcription: tuple[list, list, str] | None = None,
) -> tuple[str, str]:
    """Subtitr yozadi. Qaytaradi: (fayl_yo'li, tur) — tur: "video" yoki "srt".

    transcription berilsa (segmentlar, so'zlar, aniqlangan_til) qayta
    ishlatiladi — audio ajratish va transkripsiya o'tkazib yuboriladi
    (ko'p rejimda bir transkripsiyani bo'lishish uchun).
    """
    paths = job_paths(job_id)
    style = substyle.normalize(style)

    # AUDIO rejimi — videodan sifatli MP3 ajratib beradi (AI/subtitr yo'q,
    # eng arzon rejim). Transkripsiyani ham talab qilmaydi, shuning uchun
    # AI bilan sarlavha yasamaymiz (kontent tahlili yo'q) — oddiy nom.
    if mode == "audio":
        await progress("🎵 Ovoz (MP3) ajratilmoqda...")
        await asyncio.to_thread(extract_audio_hq, in_path, paths["audio_out"])
        _write_name(paths["audio_out"], "audio")
        return paths["audio_out"], "audio"

    if transcription is None:
        await progress("🎙 Audio ajratilmoqda...")
        await asyncio.to_thread(extract_audio, in_path, paths["audio"])
        await progress("🤖 AI nutqni tahlil qilmoqda...")
        segments, words, detected = await asyncio.to_thread(
            transcribe, paths["audio"], source_lang
        )
    else:
        segments, words, detected = transcription
    if not segments:
        raise RuntimeError("Nutq aniqlanmadi (video ovozsiz yoki juda qisqa)")

    # Whisper "gallyutsinatsiyasi"ni tozalash (soxta subtitr-krediti, SFX
    # captionlari, ketma-ket takror) — subtitr ham, lug'at ham toza bo'lsin.
    # Idempotent: keshdan kelgan (allaqachon toza) transkripsiyaga zarari yo'q.
    if settings.clean_transcription:
        segments, words = clean_segments(segments, words)
        if not segments:
            raise RuntimeError("Nutq aniqlanmadi (video ovozsiz yoki juda qisqa)")

    if source_lang and source_lang != "auto":
        eff_src = _norm_lang(source_lang)
    else:
        eff_src = _norm_lang(detected)

    # MATN rejimi — videodagi barcha gaplar (txt + pdf), video kuydirilmaydi.
    # target_lang berilsa — matnni o'sha tilga tarjima qilib chiqaramiz.
    if mode == "transcript":
        lines = [s["text"] for s in segments]
        pdf_title = "Videodagi matn"
        if target_lang:
            await progress("🌐 Matn tarjima qilinmoqda...")
            translated, _ = await asyncio.to_thread(translate_texts, lines, target_lang)
            lines = translated
            pdf_title = "Videodagi matn (tarjima)"
        full = "\n".join(lines)
        slug = await asyncio.to_thread(make_title, full, "matn")
        docgen.write_txt(paths["txt"], full)
        docgen.write_txt(paths["title"], slug)
        _write_name(paths["txt"], slug)
        await asyncio.to_thread(
            docgen.write_pdf_transcript, paths["pdf"], pdf_title, lines, _brand()
        )
        return paths["txt"], "text"

    # LUG'AT rejimi — barcha so'zlar + tarjima + tasnif (txt + pdf)
    if mode == "vocabulary":
        await progress("📚 So'zlar yig'ilib, lug'at tuzilmoqda...")
        entries = await asyncio.to_thread(build_vocabulary, segments, target_lang, eff_src)
        if not entries:
            raise RuntimeError("Lug'at uchun so'z topilmadi")
        title_src = " ".join(s.get("text", "") for s in segments)
        slug = await asyncio.to_thread(make_title, title_src, "lugat")
        docgen.write_txt_vocab(paths["txt"], "Lug'at — so'zlar va tarjimasi", entries)
        docgen.write_txt(paths["title"], slug)
        _write_name(paths["txt"], slug)
        await asyncio.to_thread(
            docgen.write_pdf_vocab,
            paths["pdf"], "Lug'at — so'zlar va tarjimasi", entries, _brand(),
        )
        return paths["txt"], "vocab"

    # Video o'lchamiga moslashgan joylashuv (shrift uslubdan, qator uzunligi)
    width, height = await asyncio.to_thread(probe_resolution, in_path)
    _is_dual = mode in ("dual", "dual_vocab")
    layout = compute_layout(width, height, substyle.font_scale(style), dual=_is_dual)
    # Ikki qatlam — har bir til bittadan qatorga sig'sin (ekran to'lmasin).
    # Dual'da matnni qisqaroq qilamiz: tarjima asl matndan uzunroq bo'ladi,
    # shuning uchun asl ~0.8 CPL bo'lsa, tarjima ham bitta qatorga sig'adi.
    max_chars = int(layout["cpl"] * 0.8) if _is_dual else layout["cpl"] * 2

    # Moslashuvchan bloklar (vaqt + o'qish tezligi)
    cues = build_cues(segments, words, max_chars)

    # Asl matnni tuzatish (o'zbek uchun)
    if eff_src in settings.correct_lang_set:
        await progress("✍️ Matn AI bilan tuzatilmoqda...")
        cues = await asyncio.to_thread(correct_segments, cues, eff_src)

    # Video/srt fayl nomini videodagi matnga qarab AI bilan qo'yamiz
    title_src = " ".join(s.get("text", "") for s in segments)
    slug = await asyncio.to_thread(make_title, title_src, "subtitr")

    if mode == "srt":
        cues_to_srt(cues, paths["srt"], layout["cpl"])
        _write_name(paths["srt"], slug)
        return paths["srt"], "srt"

    if mode == "original":
        cues_to_ass(cues, paths["ass"], width, height, settings.sub_font, layout, style)

    elif mode == "translate":
        await progress("🌐 Tarjima qilinmoqda...")
        texts = [c["text"] for c in cues]
        translated, _ = await asyncio.to_thread(translate_texts, texts, target_lang)
        trans_cues = [{**c, "text": t} for c, t in zip(cues, translated)]
        cues_to_ass(trans_cues, paths["ass"], width, height, settings.sub_font, layout, style)

    elif mode == "dual":
        await progress("🌐 Tarjima qilinmoqda...")
        texts = [c["text"] for c in cues]
        translated, _ = await asyncio.to_thread(translate_texts, texts, target_lang)
        items = [
            {"start": c["start"], "end": c["end"], "orig": c["text"], "trans": t}
            for c, t in zip(cues, translated)
        ]
        cues_to_ass_dual(items, paths["ass"], width, height, settings.sub_font, layout, style)

    elif mode == "dual_vocab":
        # Ikki qatlam subtitr + ekranda aytilgan so'zlar lug'ati (chap, suzuvchi)
        await progress("🌐 Tarjima qilinmoqda...")
        texts = [c["text"] for c in cues]
        translated, _ = await asyncio.to_thread(translate_texts, texts, target_lang)
        items = [
            {"start": c["start"], "end": c["end"], "orig": c["text"], "trans": t}
            for c, t in zip(cues, translated)
        ]
        await progress("📚 So'zlar lug'ati tuzilmoqda...")
        vocab_map = await asyncio.to_thread(
            build_vocab_map, segments, target_lang, eff_src
        )
        cues_to_ass_dual_vocab(
            items, words, vocab_map, paths["ass"],
            width, height, settings.sub_font, layout, style,
        )
    else:
        raise RuntimeError(f"Noma'lum rejim: {mode}")

    await progress("🎬 Subtitr videoga kuydirılmoqda...")
    await asyncio.to_thread(
        burn_subtitles, in_path, paths["ass"], paths["out"], height
    )
    _write_name(paths["out"], slug)
    return paths["out"], "video"


async def process_video_modes(
    in_path: str,
    job_id: str,
    progress: ProgressFn,
    *,
    modes: list[str],
    source_lang: str | None,
    target_lang: str | None,
    style: dict | None = None,
) -> list[tuple[str, str, str]]:
    """Bitta video uchun bir nechta rejimni qayta ishlaydi.

    Audio bir marta ajratiladi va transkripsiya bir marta o'tkaziladi —
    so'ng har bir rejim shu transkripsiyadan foydalanadi (tez va arzon).
    Qaytaradi: [(fayl_yo'li, tur, rejim), ...] tanlangan tartibда.
    Har rejim alohida sub-job (job_id_i) — fayllari to'qnashmaydi.
    """
    paths = job_paths(job_id)

    # Faqat "audio" rejim(lar)i so'ralsa — transkripsiya kerak emas (AI yo'q).
    # Aks holda: audioni bir marta ajratamiz, keshni tekshiramiz, kerak bo'lsa
    # transkripsiya qilamiz va keshga yozamiz (bir xil audio 7 kun qayta
    # transkripsiya qilinmaydi).
    needs_tx = any(m != "audio" for m in modes)
    transcription = None
    if needs_tx:
        from worker import cache

        await progress("🎙 Audio ajratilmoqda...")
        await asyncio.to_thread(extract_audio, in_path, paths["audio"])

        ahash = await asyncio.to_thread(cache.audio_hash, paths["audio"])
        transcription = await asyncio.to_thread(
            cache.get_transcription, ahash, source_lang
        )
        if transcription is not None:
            await progress("⚡ Oldingi tahlil topildi (keshdan)...")
        else:
            await progress("🤖 AI nutqni tahlil qilmoqda...")
            transcription = await asyncio.to_thread(
                transcribe, paths["audio"], source_lang
            )
            if transcription[0]:
                await asyncio.to_thread(
                    cache.set_transcription, ahash, source_lang, transcription
                )
        if not transcription[0]:
            raise RuntimeError("Nutq aniqlanmadi (video ovozsiz yoki juda qisqa)")

    results: list[tuple[str, str, str]] = []
    multi = len(modes) > 1
    for i, mode in enumerate(modes):
        if multi:
            await progress(f"⚙️ Rejim {i + 1}/{len(modes)} qayta ishlanmoqda...")
        out_path, kind = await process_video(
            in_path, f"{job_id}_{i}", progress,
            mode=mode, source_lang=source_lang, target_lang=target_lang,
            style=style, transcription=transcription,
        )
        results.append((out_path, kind, mode))
    return results


def cleanup_all(job_id: str) -> None:
    """job_id bilan boshlanadigan barcha ish fayllarini o'chiradi (sub-joblar ham)."""
    for path in glob.glob(os.path.join(settings.work_dir, f"{job_id}*")):
        try:
            os.remove(path)
        except OSError:
            pass
