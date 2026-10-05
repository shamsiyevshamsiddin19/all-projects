"""Bosqichlarni biriktiruvchi oqim: tayyorlash, render, sessiya."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from .core import CACHE_DIR, OUT_DIR, Segment, TMP_DIR, USAGE, VENV_DIR, Word, emit, ensure_dirs, normalize_lang_code, require_tool, reset_usage, run, safe_stem, venv_python
from .media import normalize_video_path, probe_resolution, quality_height, write_srt
from .transcribe import get_transcription
from .cache import _cache_enabled, _load_json, _save_json, cache_dir_for, load_transcription, save_transcription
from .translate import build_glossary, translate_segments
from .clean import clean_transcription, enforce_reading_speed, filter_words, polish_segments
from .vocab import build_vocabulary, entry_helper, is_translit_only
from .subtitles import burn_subtitles, write_ass
from .documents import build_reading_blocks, build_sentence_pairs, reading_meta, reading_title, reading_vocab_map, write_docx_transcript, write_docx_vocab, write_md_reading, write_pdf_reading, write_txt_reading, write_txt_transcript, write_txt_vocab


def _prepare_data(
    video_value: str,
    mode: str,
    source_lang: str,
    target_lang: str,
    quality: str | None = None,
    upscale: bool = False,
) -> dict[str, Any]:
    """Transkripsiya + (kerak bo'lsa) tarjima + lug'at. Renderlashga kerak
    bo'lgan hamma narsani lug'at (dict) qilib qaytaradi. `process()` (bir-martalik
    oqim) va `prepare` (tahrirlash oqimi) ikkalasi ham shuni ishlatadi — render
    logikasi ikki joyda takrorlanmaydi."""
    ensure_dirs()
    reset_usage()
    require_tool("ffmpeg")
    require_tool("ffprobe")
    video = normalize_video_path(video_value, quality=quality)
    stem = safe_stem(video.name)
    job_tmp = Path(tempfile.mkdtemp(prefix=stem + "_", dir=str(TMP_DIR)))

    cdir = cache_dir_for(video)
    try:
        emit("progress", message="Video o'qilmoqda", progress=0.05)
        # Checkpoint: oldingi ishdan transkripsiyani qayta ishlatamiz (Whisper
        # sekin/qimmat — takrorlamaslik uchun).
        cached_tr = load_transcription(cdir)
        if cached_tr is not None:
            original, words, detected_lang, transcriber = cached_tr
            emit("progress", message="Matn keshdan olindi", progress=0.35)
        else:
            original, words, detected_lang, transcriber = get_transcription(video, job_tmp, source_lang)
            if not original:
                raise RuntimeError("Nutq/subtitr topilmadi")
            save_transcription(cdir, original, words, detected_lang, transcriber)
        if not original:
            raise RuntimeError("Nutq/subtitr topilmadi")

        # #2 + #3: soxta matnni tozalash va aqlli birlashtirish/bo'lish.
        # (Whisper natijasiga qo'llaymiz; sozlash: SUBTITR_NO_POLISH=1 o'chiradi.)
        if os.getenv("SUBTITR_NO_POLISH", "") not in {"1", "true", "yes"}:
            cleaned = clean_transcription(original)
            if cleaned:
                original = polish_segments(cleaned) or cleaned
                # Lug'at tozalangan matndagi so'zlardan tuziladi.
                words = filter_words(words, original) or words

        raw_lang = source_lang if source_lang != "auto" else detected_lang
        effective_lang = normalize_lang_code(raw_lang)
        if raw_lang and not effective_lang:
            # Masalan "latin" — bu til emas. Tarjimaga yolg'on til berishdan
            # ko'ra, uni noma'lum deb qoldirib, foydalanuvchini ogohlantiramiz.
            emit(
                "progress",
                message=f"Diqqat: til aniqlanmadi ({raw_lang}) — "
                        "video tilini qo'lda tanlang",
                progress=0.36,
            )
        effective_lang = effective_lang or "en"
        emit("progress", message=f"Matn tayyor ({transcriber})", progress=0.35)

        needs_translation = mode in {
            "dual", "dual_vocab", "translated", "srt", "transcript", "reading", "all",
        }
        translated: list[Segment] | None = None
        provider = ""
        if needs_translation:
            emit("progress", message="Ismlar izchilligi (glossariy)", progress=0.38)
            glossary = build_glossary(original, target_lang, effective_lang)
            emit("progress", message="Tarjima qilinmoqda", progress=0.40)
            tr_cache = cdir / f"translation_{effective_lang}_{target_lang}.json"
            translated, provider = translate_segments(
                original, target_lang, effective_lang,
                cache_path=tr_cache, glossary=glossary,
            )
            # #5 — o'qishga qulay vaqtlar (juda tez o'tib ketmasin).
            translated = enforce_reading_speed(translated)

        # #5 — original subtitr vaqtlarini ham o'qishga qulay qilamiz.
        display_original = enforce_reading_speed(original)

        VOCAB_MODES = {"vocabulary", "original_vocab", "dual_vocab", "all"}
        needs_vocab = mode in VOCAB_MODES
        entries: list[dict[str, Any]] = []
        # Nom ichidagi versiya: lug'at tuzish mantig'i o'zgarganda eski
        # (yarim bo'sh) lug'at qaytarilib turmasin.
        vocab_cache = cdir / f"vocab_v2_{effective_lang}_{target_lang}.json"
        cached_vocab = _load_json(vocab_cache) if _cache_enabled() else None
        if isinstance(cached_vocab, list) and cached_vocab:
            # Tayyor lug'at bo'lsa, uni HAR QANDAY rejim ishlatadi — tekin.
            # "O'qish uchun matn" `.md` dagi {so'z|tarjima} belgilarini shundan
            # oladi, lekin lug'at YO'Q bo'lsa uni o'zi tuzmaydi: bu qo'shimcha
            # AI o'tishi bo'lib, subtitr sifatiga hech narsa qo'shmaydi.
            entries = cached_vocab
        elif needs_vocab:
            emit("progress", message="Lug'at tuzilmoqda", progress=0.58)
            entries = build_vocabulary(words, effective_lang, target_lang)
            if _cache_enabled():
                _save_json(vocab_cache, entries)
        # "Yordamchi so'z" belgisi — so'z va tildan kelib chiqadigan sof
        # hisob, AI emas. Shuning uchun uni keshdagi qiymatga ishonmasdan
        # qayta hisoblaymiz: ro'yxat kengayganda eski lug'atlar ham
        # bepul tuzaladi.
        for entry in entries:
            entry["helper"] = entry_helper(entry, effective_lang)

        width, height = probe_resolution(video)

        # Tahrirlash uchun original+tarjima bitta ro'yxatga birlashtiriladi
        # (write_ass tarjima qatorini indeks bo'yicha juftlaydi, o'z vaqtidan
        # foydalanmaydi — shuning uchun bu render uchun to'liq yetarli).
        segments: list[dict[str, Any]] = []
        for i, seg in enumerate(display_original):
            tr = translated[i].text if (translated and i < len(translated)) else ""
            segments.append({
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                # Cho'zilmagan oxir: `enforce_reading_speed` subtitr oxirini
                # keyingisiga tegguncha uzaytiradi, shuning uchun "end" dan
                # nutqdagi jimlikni bilib bo'lmaydi. "O'qish uchun matn"
                # rejimi abzatsni jimlikka qarab bo'ladi — unga asl oxir kerak.
                "rawEnd": round(original[i].end, 3) if i < len(original) else round(seg.end, 3),
                "original": seg.text,
                "translated": tr,
            })

        return {
            "video": str(video),
            "stem": stem,
            "mode": mode,
            "sourceLang": effective_lang,
            "targetLang": target_lang,
            "transcriber": transcriber,
            "translator": provider or "none",
            "width": width,
            "height": height,
            "segments": segments,
            "words": [[round(w.start, 3), round(w.end, 3), w.word] for w in words],
            "vocab": entries,
            # Haqiqatda ketgan AI so'rovlari — `prepare` -> `render` oqimida
            # ham yo'qolmasligi uchun sessiya bilan birga saqlanadi.
            "usage": dict(USAGE),
        }
    finally:
        if os.getenv("KEEP_DESKTOP_TMP", "") not in {"1", "true", "yes"}:
            shutil.rmtree(job_tmp, ignore_errors=True)


def _render_outputs(
    job: dict[str, Any],
    font_scale: float = 1.0,
    position: str = "bottom",
    sub_color: str = "#FFE680",
    orig_style: str = "box",
    quality: str | None = None,
    upscale: bool = False,
) -> dict[str, Any]:
    """`_prepare_data()` qaytargan (yoki foydalanuvchi tahrirlagan) `job`dan
    SRT/ASS/DOCX fayllar va subtitr kuydirilgan videoni tayyorlaydi."""
    ensure_dirs()
    require_tool("ffmpeg")
    require_tool("ffprobe")
    video = normalize_video_path(str(job["video"]))
    stem = safe_stem(str(job.get("stem") or video.name))
    mode = str(job["mode"])
    effective_lang = str(job.get("sourceLang") or "en")
    target_lang = str(job.get("targetLang") or "uz")
    transcriber = str(job.get("transcriber") or "")
    provider = str(job.get("translator") or "none")
    width = int(job.get("width") or 1280)
    height = int(job.get("height") or 720)

    seg_data = job.get("segments") or []
    display_original = [
        Segment(float(s["start"]), float(s["end"]), str(s.get("original", "")))
        for s in seg_data
    ]
    has_tr = any((str(s.get("translated") or "")).strip() for s in seg_data)
    translated: list[Segment] | None = (
        [Segment(float(s["start"]), float(s["end"]), str(s.get("translated") or "")) for s in seg_data]
        if has_tr else None
    )
    # O'qish rejimi uchun asl (cho'zilmagan) vaqtlar; eski sessiya faylida
    # "rawEnd" bo'lmasa, "end" ga qaytadi.
    reading_source = [
        Segment(
            float(s["start"]),
            float(s.get("rawEnd", s["end"])),
            str(s.get("original", "")),
        )
        for s in seg_data
    ]
    reading_translated: list[Segment] | None = (
        [
            Segment(float(s["start"]), float(s.get("rawEnd", s["end"])), str(s.get("translated") or ""))
            for s in seg_data
        ]
        if has_tr else None
    )
    words = [Word(float(w[0]), float(w[1]), str(w[2])) for w in (job.get("words") or [])]
    entries: list[dict[str, Any]] = list(job.get("vocab") or [])
    # Ism va o'zlashmalar kartochkaga chiqmaydi ("Чебурашка · Cheburashka"
    # ekranda joy egallaydi-yu, hech narsa o'rgatmaydi).
    vocab_map = {
        str(e["word"]): str(e["translation"])
        for e in entries
        if not is_translit_only(e)
    }

    emit("progress", message="Fayllar tayyorlanmoqda", progress=0.60)

    modes_to_render = [mode]
    if mode == "all":
        modes_to_render = ["dual_vocab", "original_vocab", "srt", "transcript", "reading", "vocabulary"]
    VOCAB_MODES = {"vocabulary", "original_vocab", "dual_vocab"}
    needs_vocab = any(m in VOCAB_MODES for m in modes_to_render)

    outputs: list[dict[str, str]] = []
    job_out_dir = OUT_DIR / stem
    job_out_dir.mkdir(parents=True, exist_ok=True)

    def add_output(kind: str, label: str, path: Path) -> None:
        outputs.append({"kind": kind, "label": label, "path": str(path), "name": path.name})

    if "srt" in modes_to_render:
        srt_orig = job_out_dir / f"{stem}_original.srt"
        write_srt(srt_orig, display_original)
        add_output("srt", "Original SRT", srt_orig)
        if translated:
            srt_uz = job_out_dir / f"{stem}_{target_lang}.srt"
            write_srt(srt_uz, translated)
            add_output("srt", "Tarjima SRT", srt_uz)

    if "transcript" in modes_to_render:
        txt = job_out_dir / f"{stem}_matn.txt"
        docx = job_out_dir / f"{stem}_matn.docx"
        write_txt_transcript(txt, display_original, translated)
        write_docx_transcript(docx, display_original, translated)
        add_output("txt", "Matn TXT", txt)
        add_output("docx", "Matn DOCX", docx)

    if "reading" in modes_to_render:
        emit("progress", message="O'qish uchun matn tayyorlanmoqda", progress=0.63)
        blocks = build_reading_blocks(reading_source)
        title = reading_title(stem)
        meta = reading_meta(blocks, effective_lang)

        # Bitta ishda hamma variant chiqadi — qaysi biri qulay bo'lsa, o'sha
        # ishlatiladi. Og'ir qism (transkripsiya, tarjima, lug'at) allaqachon
        # bajarilgan, fayllarni yozish esa deyarli bepul.
        pdf = job_out_dir / f"{stem}_oqish.pdf"
        write_pdf_reading(pdf, title, blocks, meta)
        add_output("pdf", "PDF — faqat original", pdf)

        txt = job_out_dir / f"{stem}_oqish.txt"
        write_txt_reading(txt, title, blocks, meta)
        add_output("txt", "Matn TXT", txt)

        if translated:
            tr_blocks = build_reading_blocks(reading_translated or translated)

            pdf_par = job_out_dir / f"{stem}_oqish_tarjimali.pdf"
            write_pdf_reading(
                pdf_par, title, blocks, meta,
                translated=tr_blocks, layout="parallel",
            )
            add_output("pdf", "PDF — tarjimasi bilan", pdf_par)

            pdf_split = job_out_dir / f"{stem}_oqish_alohida.pdf"
            write_pdf_reading(
                pdf_split, title, blocks, meta,
                translated=tr_blocks, layout="split",
            )
            add_output("pdf", "PDF — tarjima alohida", pdf_split)

            tr_txt = job_out_dir / f"{stem}_oqish_tarjima.txt"
            write_txt_reading(
                tr_txt, f"{title} — tarjima",
                tr_blocks, reading_meta(tr_blocks, target_lang),
            )
            add_output("txt", "Tarjima TXT", tr_txt)

            # Yordamchi saytiga yuklash uchun — gap va so'z tarjimalari
            # faylning ichida bo'ladi, sayt tarjimonga murojaat qilmaydi.
            md = job_out_dir / f"{stem}_oqish.md"
            write_md_reading(
                md, title,
                build_sentence_pairs(reading_source, reading_translated or translated),
                reading_vocab_map(entries),
            )
            add_output("md", "Yordamchi uchun MD", md)

    if "vocabulary" in modes_to_render:
        txt = job_out_dir / f"{stem}_lugat.txt"
        docx = job_out_dir / f"{stem}_lugat.docx"
        write_txt_vocab(txt, entries)
        write_docx_vocab(docx, entries)
        add_output("txt", "Lug'at TXT", txt)
        add_output("docx", "Lug'at DOCX", docx)

    render_modes = [
        m for m in modes_to_render
        if m in {"original", "dual", "original_vocab", "dual_vocab", "translated"}
    ]
    n_render = max(1, len(render_modes))
    for i, render_mode in enumerate(render_modes):
        emit("progress", message=f"ASS tayyorlanmoqda: {render_mode}", progress=0.66)
        ass = job_out_dir / f"{stem}_{render_mode}.ass"
        out = job_out_dir / f"{stem}_{render_mode}.mp4"
        use_trans = translated if render_mode in {"dual", "dual_vocab", "translated"} else None
        use_words = words if render_mode in {"original_vocab", "dual_vocab"} else None
        write_ass(
            ass, display_original, use_trans, use_words, vocab_map, width, height,
            font_scale=font_scale, position=position, trans_color=sub_color,
            orig_style=orig_style, show_original=render_mode != "translated",
        )
        add_output("ass", f"{render_mode} ASS", ass)
        # Render progressini bir necha video orasida bo'lib ko'rsatamiz.
        lo = 0.70 + (0.28 * i / n_render)
        hi = 0.70 + (0.28 * (i + 1) / n_render)
        burn_subtitles(
            video, ass, out, progress_lo=lo, progress_hi=hi, label=render_mode,
            max_height=quality_height(quality), upscale=upscale,
        )
        add_output("video", f"{render_mode} video", out)

    # Vocab-li video rejimlar uchun lug'at faylini ham saqlab qo'yamiz.
    if needs_vocab and mode in {"dual_vocab", "original_vocab"}:
        txt = job_out_dir / f"{stem}_lugat.txt"
        if not txt.exists():
            write_txt_vocab(txt, entries)
        add_output("txt", "Lug'at TXT", txt)

    emit("progress", message="Yakunlandi", progress=1.0)
    return {
        "video": str(video),
        "mode": mode,
        "sourceLang": effective_lang,
        "targetLang": target_lang,
        "translator": provider,
        "transcriber": transcriber,
        "outputs": outputs,
        "outDir": str(job_out_dir),
        "usage": dict(job.get("usage") or USAGE),
    }


def _session_path_for(job: dict[str, Any]) -> Path:
    d = CACHE_DIR / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(str(job.get("video", "")).encode("utf-8", "replace")).hexdigest()[:10]
    return d / f"{safe_stem(str(job.get('stem') or 'session'))}_{key}.json"


def prepare_session(video_value: str, mode: str, source_lang: str, target_lang: str,
                    quality: str | None = None) -> dict[str, Any]:
    """Renderlashdan OLDIN transkripsiya+tarjimani tayyorlab, seans faylига saqlaydi.
    Foydalanuvchi tarjimalarni ko'rib/tahrirlab, keyin `render` bilan yakunlaydi."""
    job = _prepare_data(video_value, mode, source_lang, target_lang, quality=quality)
    session_path = _session_path_for(job)
    session_path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    return {
        "session": str(session_path),
        "video": job["video"],
        "mode": job["mode"],
        "sourceLang": job["sourceLang"],
        "targetLang": job["targetLang"],
        "transcriber": job["transcriber"],
        "translator": job["translator"],
        "segments": job["segments"],
        "vocabCount": len(job.get("vocab") or []),
    }


def render_session(
    session_path: str,
    segments_path: str | None = None,
    font_scale: float = 1.0,
    position: str = "bottom",
    sub_color: str = "#FFE680",
    orig_style: str = "box",
    quality: str | None = None,
    upscale: bool = False,
) -> dict[str, Any]:
    """Seans faylini (va agar berilgan bo'lsa, tahrirlangan segmentlarni) o'qib,
    videoni renderlaydi."""
    data = _load_json(Path(session_path))
    if not isinstance(data, dict) or not data.get("segments"):
        raise RuntimeError("Seans fayli topilmadi yoki buzilgan.")
    if segments_path:
        edited = _load_json(Path(segments_path))
        if isinstance(edited, list) and edited:
            # Foydalanuvchi tahrirlagan segmentlar butunlay almashtiradi.
            data["segments"] = edited
    return _render_outputs(
        data, font_scale=font_scale, position=position,
        sub_color=sub_color, orig_style=orig_style, quality=quality,
        upscale=upscale,
    )


def process(
    video_value: str,
    mode: str,
    source_lang: str,
    target_lang: str,
    font_scale: float = 1.0,
    position: str = "bottom",
    sub_color: str = "#FFE680",
    orig_style: str = "box",
    quality: str | None = None,
    upscale: bool = False,
) -> dict[str, Any]:
    job = _prepare_data(video_value, mode, source_lang, target_lang, quality=quality)
    return _render_outputs(
        job, font_scale=font_scale, position=position,
        sub_color=sub_color, orig_style=orig_style, quality=quality,
        upscale=upscale,
    )


def install_deps() -> None:
    if getattr(sys, 'frozen', False):
        emit("done", message="Dastur qadoqlangan, paketlar ichida mavjud")
        return
        
    packages = [
        "python-dotenv>=1.0.0",
        "groq>=0.11.0",
        "openai>=1.40.0",
        "google-genai>=1.0.0",
        "anthropic>=0.40.0",
        "python-docx>=1.1.2",
        "reportlab>=4.0.0",
    ]
    # Debian/Ubuntu (PEP 668) tizim Python'iga `pip install --user` ni bloklaydi,
    # shuning uchun paketlar dastur yonidagi virtual muhitga o'rnatiladi.
    python = venv_python()
    if not python.exists():
        emit("progress", message="Virtual muhit yaratilmoqda", progress=0.05)
        proc = run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if proc.returncode != 0:
            raise RuntimeError(
                (proc.stderr[-800:] or "venv yaratib bo'lmadi")
                + "\n(Ubuntu: `sudo apt install python3-venv` kerak bo'lishi mumkin)"
            )
    emit("progress", message="Python paketlar o'rnatilmoqda", progress=0.1)
    proc = run([str(python), "-m", "pip", "install", "--upgrade", *packages])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1000:] or "pip install xato")
    emit("done", message="Paketlar o'rnatildi")
