"""ASS subtitr yasash va videoga kuydirish."""
from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import NamedTuple

from .core import FFMPEG, ROOT, Segment, Word, _env_float, emit, normalize_word, require_tool, run, wrap_lines
from .media import probe_duration_seconds, probe_resolution, seconds_to_ass_time


def ass_escape(text: str) -> str:
    return (text or "").replace("{", "(").replace("}", ")").replace("\n", r"\N")


def ass_color(hex_color: str, alpha: str = "00") -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        h = "FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


def inline_color(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        h = "FFFFFF"
    return "{\\c&H" + (h[4:6] + h[2:4] + h[0:2]).upper() + "&}"


def layout_for(width: int, height: int, dual: bool, font_scale: float = 1.0) -> dict[str, int]:
    ar = width / max(1, height)
    base = width if ar < 0.85 else height
    # Subtitr balandlikning ~4-4.5% i bo'lgani o'qishga qulay; oldingi 3.1-3.5%
    # 1080p da 33 px chiqib, ekranda mayda va kuchsiz ko'rinardi.
    font_size = max(18, round(base * (0.045 if not dual else 0.040) * font_scale))
    margin_lr = max(24, round(width * 0.06))
    cpl = max(18, min(48, int((width - margin_lr * 2) / (font_size * 0.52))))
    return {
        "font": font_size,
        "vocab_font": max(16, round(font_size * 0.9)),
        "margin_lr": margin_lr,
        "margin_v": max(28, round(height * (0.07 if ar >= 1.0 else 0.15))),
        "cpl": cpl,
        # Qora kontur matnni fondan ajratadi, lekin 0.13 da u haddan tashqari
        # qalin chiqardi: Montserrat Black o'zi og'ir shrift, ustiga keng
        # halqa qo'shilsa harflarning ichi (o, a, e) yopilib, matn iflos
        # ko'rinadi. 0.062 — 1080p da ~3 px: yorug' sahnada ham ajralib
        # turadi, lekin harf shakli buzilmaydi.
        "outline": max(2, round(font_size * _env_float("SUB_OUTLINE_RATIO", 0.062))),
        # Sariq quti uchun: ichki bo'shliq va harflar orasi (montaj uslubida
        # matn quti ichida biroz keng joylashadi).
        "box_pad": max(4, round(font_size * 0.16)),
        "box_spacing": max(0, round(font_size * 0.04)),
        "line_h": round(font_size * 1.28),
        "vocab_outline": max(2, round(font_size * 0.07)),
        "vocab_pad": max(5, round(font_size * 0.20)),
    }


# Subtitr shrifti: dastur yonidagi `fonts/` da qalin (Black) shrift bo'lsa
# o'shani ishlatamiz — tizimdagi Noto Sans faqat Bold (700) gacha bo'lgani
# uchun matn ekranda kuchsiz ko'rinardi. Topilmasa Noto Sans'ga qaytamiz.
FONTS_DIR = ROOT / "fonts"
_BUNDLED_FONT = FONTS_DIR / "Montserrat-Black.ttf"


def subtitle_font_name() -> str:
    override = os.getenv("SUB_FONT", "").strip()
    if override:
        return override
    return "Montserrat Black" if _BUNDLED_FONT.exists() else "Noto Sans"


def _filter_escape(value: str) -> str:
    """ffmpeg filtr argumenti uchun yo'lni himoyalash."""
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def ass_fonts_option() -> str:
    """`ass` filtriga qo'shiladigan `:fontsdir=...` (shrift bo'lsa)."""
    if not _BUNDLED_FONT.exists():
        return ""
    return ":fontsdir=" + _filter_escape(str(FONTS_DIR))


# Asl matn uslubi: "plain" — oq matn + qora kontur (eski ko'rinish),
# "box" — sariq to'ldirilgan quti ustida qora qalin matn (montaj uslubi).
BOX_FILL = os.getenv("SUB_BOX_COLOR", "#FFD400")
# Lug'at kartochkasining foni (yarim shaffof to'q rang).
VOCAB_BG = os.getenv("SUB_VOCAB_BG", "#0B1020")
VOCAB_BG_ALPHA = os.getenv("SUB_VOCAB_BG_ALPHA", "3C")
BOX_TEXT = os.getenv("SUB_BOX_TEXT_COLOR", "#000000")


def ass_header(
    width: int,
    height: int,
    layout: dict[str, int],
    alignment: int = 2,
    orig_style: str = "plain",
) -> str:
    font = subtitle_font_name()
    outline = layout["outline"]
    # Soya YO'Q. ASS soyasi — matnning o'ngga-pastga surilgan qora nusxasi;
    # kontur bilan birga u harflarni ikkilantirib, xiralashtirib yuboradi.
    # Ajratish uchun konturning o'zi yetarli.
    shadow = int(_env_float("SUB_SHADOW", 0.0))
    fmt = (
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    )
    # Asl matn: oddiy (kontur) yoki sariq quti (BorderStyle=3 — to'ldirilgan fon).
    if orig_style == "box":
        bottom = (
            f"Style: Bottom,{font},{layout['font']},{ass_color(BOX_TEXT)},&H000000FF,"
            f"{ass_color(BOX_FILL)},&H00000000,0,0,0,0,100,100,{layout['box_spacing']},0,3,"
            f"{layout['box_pad']},0,{alignment},{layout['margin_lr']},{layout['margin_lr']},"
            f"{layout['margin_v']},1\n"
        )
    else:
        bottom = (
            f"Style: Bottom,{font},{layout['font']},{ass_color('#FFFFFF')},&H000000FF,"
            f"{ass_color('#000000')},&H00000000,1,0,0,0,100,100,0,0,1,{outline},"
            f"{shadow},{alignment},{layout['margin_lr']},{layout['margin_lr']},"
            f"{layout['margin_v']},1\n"
        )
    # Tarjima qatori alohida uslub — quti faqat asl matnga tegishli bo'lsin.
    trans = (
        f"Style: Trans,{font},{layout['font']},{ass_color('#FFFFFF')},&H000000FF,"
        f"{ass_color('#000000')},&H00000000,1,0,0,0,100,100,0,0,1,{outline},"
        f"{shadow},{alignment},{layout['margin_lr']},{layout['margin_lr']},"
        f"{layout['margin_v']},1\n"
    )
    # Lug'at kartochkasi: fonsiz, qalin qora konturli matn.
    # To'ldirilgan fon (BorderStyle=3) yaramadi — libass qutini rang o'zgargan
    # joyda uzib qo'yadi, natijada so'z, nuqta va tarjima uchta alohida
    # to'rtburchakka bo'linib, chetlari tishli bo'lib ko'rinardi.
    vocab = (
        f"Style: Vocab,{font},{layout['vocab_font']},{ass_color('#FFFFFF')},&H000000FF,"
        f"{ass_color('#000000')},{ass_color('#000000', '60')},0,0,0,0,100,100,"
        f"{layout['box_spacing']},0,1,{layout['vocab_outline']},0,7,"
        f"{layout['margin_lr']},{layout['margin_lr']},{layout['margin_v']},1\n"
        # Kartochka foni. Hiyla: fon ham AYNAN o'sha matn bilan chiziladi,
        # lekin harflari butunlay shaffof (PrimaryColour alpha = FF) va
        # BorderStyle=3 — libass matn kengligini o'zi o'lchab, uzluksiz quti
        # chizadi. Shu bilan matn kengligini taxminlash kerak bo'lmaydi;
        # rang o'zgarishi ham yo'q, demak quti bo'laklarga ajralmaydi.
        f"Style: VocabBg,{font},{layout['vocab_font']},&HFF000000,&H000000FF,"
        f"{ass_color(VOCAB_BG, VOCAB_BG_ALPHA)},&H00000000,0,0,0,0,100,100,"
        f"{layout['box_spacing']},0,3,{layout['vocab_pad']},0,7,"
        f"{layout['margin_lr']},{layout['margin_lr']},{layout['margin_v']},1\n\n"
    )
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        + fmt + bottom + trans + vocab +
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def write_ass(
    path: Path,
    original: list[Segment],
    translated: list[Segment] | None,
    vocab_words: list[Word] | None,
    vocab_map: dict[str, str],
    width: int,
    height: int,
    font_scale: float = 1.0,
    position: str = "bottom",
    trans_color: str = "#FFE680",
    orig_style: str = "plain",
    show_original: bool = True,
) -> None:
    """`show_original=False` bo'lsa ekranda faqat tarjima qatori qoladi
    ("Faqat tarjima" rejimi). Shunda qator yolg'iz bo'lgani uchun shrift
    ham kattaroq olinadi va o'z rangida (`trans_color`) chiqadi."""
    dual = show_original and translated is not None
    layout = layout_for(width, height, dual=dual, font_scale=font_scale)
    alignment = 8 if position == "top" else 2  # ASS: 8=tepa markaz, 2=past markaz
    line_h = layout["line_h"]
    gap = max(2, round(layout["font"] * 0.12))
    with path.open("w", encoding="utf-8") as f:
        f.write(ass_header(width, height, layout, alignment=alignment, orig_style=orig_style))
        for i, seg in enumerate(original):
            start = seconds_to_ass_time(seg.start)
            end = seconds_to_ass_time(seg.end)
            orig_lines = (
                wrap_lines(seg.text, layout["cpl"] + (5 if dual else 0), 2)
                if show_original else []
            )
            trans_lines: list[str] = []
            if translated and i < len(translated):
                trans_lines = wrap_lines(
                    translated[i].text, layout["cpl"] + (5 if dual else 0), 2
                )

            if orig_style == "box":
                # Sariq quti faqat asl matnni o'rashi kerak, shuning uchun asl
                # va tarjima alohida hodisa bo'lib yoziladi va MarginV bilan
                # ustma-ust qo'yiladi (quti tarjima qatorini ham yutmasin).
                if alignment == 8:  # tepada: asl yuqorida
                    orig_v = layout["margin_v"]
                    trans_v = orig_v + (
                        len(orig_lines) * line_h + gap if orig_lines else 0
                    )
                else:               # pastda: tarjima eng pastda
                    trans_v = layout["margin_v"]
                    orig_v = trans_v + (
                        len(trans_lines) * line_h + gap if trans_lines else 0
                    )
                if orig_lines:
                    body = r"\N".join(ass_escape(x) for x in orig_lines)
                    f.write(f"Dialogue: 0,{start},{end},Bottom,,0,0,{orig_v},,{body}\n")
                if trans_lines:
                    body = inline_color(trans_color) + r"\N".join(
                        ass_escape(x) for x in trans_lines
                    )
                    f.write(f"Dialogue: 0,{start},{end},Trans,,0,0,{trans_v},,{body}\n")
                continue

            lines: list[str] = []
            if orig_lines:
                lines.append(inline_color("#FFFFFF") + r"\N".join(ass_escape(x) for x in orig_lines))
            if trans_lines:
                lines.append(inline_color(trans_color) + r"\N".join(ass_escape(x) for x in trans_lines))
            if lines:
                joined = r"\N".join(lines)
                f.write(f"Dialogue: 0,{start},{end},Bottom,,0,0,0,,{joined}\n")

        if vocab_words:
            x = max(24, round(width * 0.04))
            base_y = round(height * 0.85)
            line_height = round(layout["vocab_font"] * 1.5)
            
            # Uzluksiz tepaga qarab harakatlanish (Scroll) mantig'i:
            # Ekranning 75% qismini bosib o'tadi
            distance = round(height * 0.75)
            target_y = base_y - distance
            duration_sec = 4.0
            
            # Tezlik = Masofa / Vaqt (piksellar / sekund)
            speed = distance / duration_sec
            
            # Bir-birining ustiga chiqib ketmasligi uchun 
            # ikkita so'z orasidagi minimal vaqt oralig'i
            min_time_gap = line_height / speed
            max_drift = _env_float("SUBTITR_VOCAB_MAX_DRIFT", 3.0)
            # Bir so'z ketma-ket takrorlanganda ikkita bir xil kartochka
            # yonma-yon suzib chiqadi — shuni oldini olamiz.
            repeat_window = _env_float("SUBTITR_VOCAB_REPEAT_WINDOW", 20.0)
            shown_at: dict[str, float] = {}

            sep = "  ·  "

            last_start_time = -999.0
            
            for item in vocab_words:
                key = normalize_word(item.word)
                tr = vocab_map.get(key, "")
                if not tr:
                    continue
                prev = shown_at.get(key)
                if prev is not None and item.start - prev < repeat_window:
                    continue
                
                # So'z paydo bo'ladigan vaqtni hisoblash (oldingi so'zdan yetarlicha uzoqda bo'lishi kerak)
                actual_start = max(item.start, last_start_time + min_time_gap)
                # Nutq zich bo'lsa surilish to'planib ketadi va so'z aytilganidan
                # ancha keyin chiqadi. Bunday so'zni ko'rsatmaymiz — noto'g'ri
                # joyda chiqqan so'z tomoshabinni chalg'itadi.
                if actual_start - item.start > max_drift:
                    continue
                actual_end = actual_start + duration_sec
                last_start_time = actual_start
                shown_at[key] = item.start

                start = seconds_to_ass_time(actual_start)
                end = seconds_to_ass_time(actual_end)
                word = ass_escape(key)
                translation = ass_escape(tr)

                # Fon: aynan o'sha matn, lekin harflari ko'rinmas — libass
                # kengligini o'zi o'lchab, uzluksiz quti chizadi.
                override = "{\\fad(250,450)\\move(%d,%d,%d,%d)}" % (
                    x, base_y, x, target_y
                )
                plain = f"{word}{sep}{translation}"
                f.write(f"Dialogue: 0,{start},{end},VocabBg,,0,0,0,,{override}{plain}\n")

                # Ko'rinadigan matn — xuddi shu joyda, fon ustida.
                body = (
                    f"{override}{inline_color('#FFFFFF')}{word}"
                    f"{inline_color('#8A93A6')}{sep}"
                    f"{inline_color(trans_color)}{translation}"
                )
                f.write(f"Dialogue: 1,{start},{end},Vocab,,0,0,0,,{body}\n")


_HW_ENCODER_CACHE: str | None = None
VAAPI_DEVICE = os.getenv("VAAPI_DEVICE", "/dev/dri/renderD128")


class EncoderChoice(NamedTuple):
    """One video encoder recipe: the codec, its quality args, a human name, any
    args that must precede the input (VAAPI device), and filters appended to the
    subtitle filter chain (VAAPI needs the frames uploaded to the GPU)."""

    codec: str
    args: list[str]
    name: str
    pre_args: list[str] = []
    filters: list[str] = []


def _encoder_works(choice: EncoderChoice) -> bool:
    proc = run(
        [
            FFMPEG, "-hide_banner", "-loglevel", "error",
            *choice.pre_args,
            "-f", "lavfi", "-i", "color=c=black:s=128x128:d=0.1",
            *(["-vf", ",".join(choice.filters)] if choice.filters else []),
            "-c:v", choice.codec, *choice.args, "-f", "null", "-",
        ]
    )
    return proc.returncode == 0


def pick_video_encoder() -> EncoderChoice:
    """Return the encoder recipe for the subtitle burn.

    Prefers a working GPU encoder (NVIDIA/Intel/AMD) — much faster on long
    films — falling back to CPU libx264. On Linux the vendor-neutral path is
    VAAPI (AMD/Intel drivers ship it; NVENC/QSV/AMF are mostly Windows).
    Configurable via SUB_ENCODER (auto|nvenc|qsv|amf|vaapi|x264).
    """
    # 25 juda past edi — kuydirilgan matn chetlari yemirilib, "xira" ko'rinardi.
    q = os.getenv("SUB_CRF", "20")
    x264 = EncoderChoice(
        "libx264",
        ["-preset", os.getenv("SUB_PRESET", "veryfast"), "-crf", q],
        "libx264 (CPU)",
    )
    presets: dict[str, EncoderChoice] = {
        "nvenc": EncoderChoice(
            "h264_nvenc", ["-preset", "p5", "-rc", "vbr", "-cq", q, "-b:v", "0"], "NVIDIA NVENC"
        ),
        "qsv": EncoderChoice("h264_qsv", ["-global_quality", q, "-preset", "faster"], "Intel QSV"),
        "amf": EncoderChoice("h264_amf", ["-rc", "cqp", "-qp_i", q, "-qp_p", q], "AMD AMF"),
        "vaapi": EncoderChoice(
            "h264_vaapi",
            ["-rc_mode", "CQP", "-qp", q],
            "VAAPI (GPU)",
            ["-vaapi_device", VAAPI_DEVICE],
            ["format=nv12", "hwupload"],
        ),
        "x264": x264,
    }
    choice = os.getenv("SUB_ENCODER", "auto").strip().lower()
    if choice in presets:
        return presets[choice]

    global _HW_ENCODER_CACHE
    if _HW_ENCODER_CACHE is None:
        _HW_ENCODER_CACHE = "x264"
        candidates = ["nvenc", "qsv", "amf"]
        if os.path.exists(VAAPI_DEVICE):
            candidates.append("vaapi")
        for name in candidates:
            try:
                if _encoder_works(presets[name]):
                    _HW_ENCODER_CACHE = name
                    break
            except Exception:
                continue
    return presets.get(_HW_ENCODER_CACHE, x264)


def burn_subtitles(
    video: Path,
    ass_path: Path,
    out_path: Path,
    progress_lo: float = 0.76,
    progress_hi: float = 0.98,
    label: str = "",
    max_height: int = 0,
    upscale: bool = False,
) -> None:
    require_tool("ffmpeg")
    total = probe_duration_seconds(video)
    suffix = f": {label}" if label else ""
    # O'lcham o'zgartirish subtitrdan OLDIN: shunda matn to'g'ridan-to'g'ri
    # chiqish kadriga chiziladi va tiniq bo'ladi (tayyor kadrni cho'zish emas).
    #
    # `upscale` — manba past sifatli bo'lsa ham kattaroq kadrga chiqarish.
    # Diqqat: bu tasvirga tafsilot QO'SHMAYDI; foydasi shundaki, subtitr va
    # lug'at matni vektor sifatida yangi o'lchamda chiziladi — ular haqiqatan
    # tiniq chiqadi. Shu sababli yumshoq `unsharp` ham qo'shiladi.
    scale_filter = ""
    if max_height:
        _, src_h = probe_resolution(video)
        if src_h and src_h > max_height:
            scale_filter = f"scale=-2:{max_height}:flags=lanczos"
        elif src_h and upscale and src_h < max_height:
            sharpen = os.getenv("SUB_UPSCALE_SHARPEN", "unsharp=5:5:0.7:5:5:0.0")
            scale_filter = f"scale=-2:{max_height}:flags=lanczos"
            if sharpen:
                scale_filter += "," + sharpen

    def _run(choice: EncoderChoice) -> tuple[int, str]:
        enc_name = choice.name
        emit("progress", message=f"Video render qilinmoqda ({enc_name}){suffix}", progress=progress_lo)
        vf = ",".join(
            ([scale_filter] if scale_filter else [])
            + [f"ass={ass_path.name}{ass_fonts_option()}", *choice.filters]
        )
        cmd = [
            FFMPEG, "-y",
            *choice.pre_args,
            "-i", str(video),
            "-vf", vf,
            "-c:v", choice.codec, *choice.args,
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-progress", "pipe:1", "-nostats",
            str(out_path),
        ]
        # Streamli — render foizini jonli ko'rsatish uchun `-progress` (stdout)
        # o'qiymiz; stderr'ni alohida oqimda bo'shatamiz (aks holda buferi to'lib
        # ffmpeg'ni bloklaydi).
        proc = subprocess.Popen(
            cmd, cwd=str(ass_path.parent),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        stderr_chunks: list[str] = []

        def _drain_stderr() -> None:
            if proc.stderr is not None:
                for ln in proc.stderr:
                    stderr_chunks.append(ln)

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()
        last_pct = -1
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("out_time_us=") and total > 0:
                try:
                    secs = int(line.split("=", 1)[1]) / 1_000_000.0
                except ValueError:
                    continue
                frac = max(0.0, min(1.0, secs / total))
                pct = round(frac * 100)
                if pct != last_pct:
                    last_pct = pct
                    emit(
                        "progress",
                        message=f"Video render ({enc_name}){suffix} {pct}%",
                        progress=progress_lo + (progress_hi - progress_lo) * frac,
                    )
        proc.wait()
        stderr_thread.join(timeout=5)
        return proc.returncode, "".join(stderr_chunks)

    choice = pick_video_encoder()
    code, err = _run(choice)
    if code != 0 and choice.codec != "libx264":
        # Apparat kodlash uzildi (drayver/format) — libx264 (CPU) ga qaytamiz.
        global _HW_ENCODER_CACHE
        _HW_ENCODER_CACHE = "x264"
        code, err = _run(
            EncoderChoice(
                "libx264",
                ["-preset", os.getenv("SUB_PRESET", "veryfast"), "-crf", os.getenv("SUB_CRF", "20")],
                "libx264 (CPU)",
            )
        )
    if code != 0:
        raise RuntimeError("Video render xato: " + (err[-900:] or "noma'lum"))
