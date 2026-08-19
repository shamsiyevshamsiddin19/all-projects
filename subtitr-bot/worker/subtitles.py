"""Cue (blok)lardan .srt / .ass yaratish.

Bloklar worker/cues.py da quriladi (vaqt + o'qish tezligi). Bu modul
ularni ekranga chiqarish uchun fayllarga yozadi: matnni qatorlarga
bo'ladi va uslub beradi (toza kontur).
"""
from __future__ import annotations

import math
import textwrap

from worker import substyle


def _format_srt_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_ass_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    cs = int(round(seconds * 100))
    s = cs // 100
    cs %= 100
    h = s // 3600
    m = (s % 3600) // 60
    s %= 60
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_text(text: str) -> str:
    """ASS uchun tozalash (override belgilarini zararsizlantirish)."""
    return (text or "").replace("{", "(").replace("}", ")")


# Yangi qator boshida tabiiy ko'rinadigan so'zlar — ulardan OLDIN bo'lish afzal
# (bog'lovchi/predlog yangi qatorni boshlasin, oldingi qator oxirida osilib qolmasin)
_BREAK_BEFORE = {
    "and", "but", "or", "so", "because", "with", "for", "to", "that", "which",
    "when", "if", "while", "as",
    "va", "ammo", "lekin", "chunki", "bilan", "uchun", "ham", "yoki", "agar",
    "и", "но", "а", "что", "чтобы", "для", "когда", "если", "потому", "как",
}


def _split_two_lines(text: str, cpl: int) -> list[str]:
    """Matnni grammatik chegarada 2 qatorga bo'ladi (Netflix/BBC uslubi).

    Tinish belgisidan keyin va bog'lovchi/predlogdan oldin bo'lishni afzal
    ko'radi; teng holatda pastki qator uzunroq (bottom-heavy).
    """
    words = text.split()
    if len(words) < 2:
        return [text]
    best = None  # (ball, [yuqori, pastki])
    for i in range(1, len(words)):
        top = " ".join(words[:i])
        bot = " ".join(words[i:])
        if len(top) > cpl or len(bot) > cpl:
            continue
        score = 0.0
        if top[-1:] in ",.!?;:…—–":          # tinish belgisidan keyin bo'lish
            score += 10
        if words[i].strip(",.!?;:—–").lower() in _BREAK_BEFORE:
            score += 6
        longest = max(len(top), len(bot)) or 1
        score += 3.0 - 3.0 * abs(len(top) - len(bot)) / longest  # balans
        if len(bot) >= len(top):              # bottom-heavy bonus
            score += 1
        if best is None or score > best[0]:
            best = (score, [top, bot])
    if best:
        return best[1]
    # Hech qaysi nuqta ikkala qatorni ≤cpl qila olmadi — so'z YO'QOTMASDAN
    # greedy to'ldiramiz (2-qator cpl dan oshishi mumkin, lekin matn to'liq).
    top, j = "", 0
    while j < len(words) - 1 and len(f"{top} {words[j]}".strip()) <= cpl:
        top = f"{top} {words[j]}".strip()
        j += 1
    if not top:                 # birinchi so'zning o'zi cpl dan uzun
        top, j = words[0], 1
    return [top, " ".join(words[j:])]


def wrap_lines(text: str, cpl: int, max_lines: int = 2) -> list[str]:
    """Matnni ≤max_lines balansli, grammatik qatorga bo'ladi (har biri ~cpl belgi)."""
    text = " ".join((text or "").split())
    if not text:
        return []
    if len(text) <= cpl:
        return [text]
    if max_lines == 2:
        return _split_two_lines(text, cpl)
    lines = textwrap.wrap(text, width=cpl)
    if len(lines) > max_lines:
        balanced = max(cpl, math.ceil(len(text) / max_lines))
        lines = textwrap.wrap(text, width=balanced)[:max_lines]
    return lines


def _ass_header(width: int, height: int, font: str, layout: dict,
                style: dict) -> str:
    primary = substyle.ass_color(style["text_color"])
    outline_c = substyle.ass_color(style["outline_color"])
    bold = 1 if style["bold"] else 0
    align = substyle.alignment(style)
    if style["box"]:
        border_style = 3  # noshaffof quti
        back = substyle.ass_color(style["outline_color"], "40")  # yarim shaffof
        shadow = 0  # quti bilan soya keraksiz
    else:
        border_style = 1  # faqat kontur
        back = "&H00000000"
        shadow = layout.get("shadow", 0)  # yengil soya — fonda ajralib tursin
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{font},{layout['font_size']},{primary},&H000000FF,"
        f"{outline_c},{back},{bold},0,0,0,100,100,0,0,{border_style},"
        f"{layout['outline']},{shadow},{align},"
        f"{layout['margin_lr']},{layout['margin_lr']},{layout['margin_v']},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )


def cues_to_srt(cues: list[dict], srt_path: str, cpl: int) -> None:
    with open(srt_path, "w", encoding="utf-8") as f:
        index = 1
        for c in cues:
            lines = wrap_lines(c["text"], cpl)
            if not lines:
                continue
            start = _format_srt_ts(c["start"])
            end = _format_srt_ts(c["end"])
            f.write(f"{index}\n{start} --> {end}\n" + "\n".join(lines) + "\n\n")
            index += 1


def cues_to_ass(cues: list[dict], ass_path: str, width: int, height: int,
                font: str, layout: dict, style: dict) -> None:
    """Bitta tilli subtitr (original yoki tarjima) — uslub bo'yicha."""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(_ass_header(width, height, font, layout, style))
        for c in cues:
            lines = wrap_lines(c["text"], layout["cpl"])
            if not lines:
                continue
            start = _format_ass_ts(c["start"])
            end = _format_ass_ts(c["end"])
            body = r"\N".join(_ass_text(ln) for ln in lines)
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{body}\n")


def _write_dual_events(f, items: list[dict], layout: dict, style: dict) -> None:
    """Ikki qatlam subtitr Dialogue qatorlarini yozadi (Default style, past)."""
    c_orig = substyle.ass_inline(style["text_color"])
    c_trans = substyle.ass_inline(style["trans_color"])
    wrap_w = layout["cpl"] + 4
    for it in items:
        start = _format_ass_ts(it["start"])
        end = _format_ass_ts(it["end"])
        orig_lines = wrap_lines(it.get("orig", ""), wrap_w, max_lines=2)
        trans_lines = wrap_lines(it.get("trans", ""), wrap_w, max_lines=2)
        parts = []
        if orig_lines:
            parts.append(c_orig + r"\N".join(_ass_text(x) for x in orig_lines))
        if trans_lines:
            parts.append(c_trans + r"\N".join(_ass_text(x) for x in trans_lines))
        if not parts:
            continue
        body = r"\N".join(parts)
        f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{body}\n")


def cues_to_ass_dual(items: list[dict], ass_path: str, width: int, height: int,
                     font: str, layout: dict, style: dict) -> None:
    """Ikki qatlam: yuqori qatori asl til (matn rangi), pastki qatori tarjima
    (tarjima rangi). items: [{"start","end","orig","trans"}, ...]
    """
    # Dual'da har bir til ko'pi bilan 2 qator (jami ≤4) — lekin matn qisqartilgan
    # (pipeline max_chars=0.8*cpl) bo'lgani uchun odatda 1 qatordan chiqadi.
    # Kengroq wrap (cpl+4) qo'llaymiz: bitta uzun so'z qatorni buzmasin.
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(_ass_header(width, height, font, layout, style))
        _write_dual_events(f, items, layout, style)


# ---------------------------------------------------------------- dual + lug'at
# Ekranда aytilgan so'zlar chap tomonда tarjimasi bilan paydo bo'lib, tepaga
# suzib chiqadi (til o'rganish rejimi). "Subtitle app" desktop ilovasidan
# ko'chirilgan: scroll animatsiya + pop-in/pop-out (\move, \fad, \blur, \fsc).

# Lug'at solishtiruvi uchun so'zni tozalaydi (kichik harf, chekka tinishsiz,
# apostrof variantlari birxillashtiriladi). vocab.build_vocab_map ham SHU
# funksiyadan foydalanadi — kalitlar aynan mos kelsin (aks holda so'z topilmaydi).
_WORD_STRIP = "`'\".,!?;:()[]{}«»—–…"


def normalize_word(word: str) -> str:
    w = (word or "").lower().strip(_WORD_STRIP)
    return w.replace("’", "'").replace("ʼ", "'").replace("ʻ", "'")


def _vocab_style_line(font: str, layout: dict) -> str:
    """Chap-tepa (align 7) noshaffof quti ichida lug'at uslubi."""
    vocab_font = max(16, round(layout["font_size"] * 0.9))
    outline = max(1, layout.get("outline", 2) // 2)
    text_c = substyle.ass_color("#FFFFFF")
    box_c = substyle.ass_color("#08111F")           # to'q ko'k quti
    back_c = substyle.ass_color("#08111F", "55")    # yarim shaffof orqa fon
    return (
        f"Style: Vocab,{font},{vocab_font},{text_c},&H000000FF,"
        f"{box_c},{back_c},1,0,0,0,100,100,0,0,3,{outline},1,7,24,24,24,1\n"
    )


def _write_vocab_scroll(f, words: list[dict], vocab_map: dict[str, str],
                        width: int, height: int, layout: dict) -> None:
    """So'zlar chap tomonда paydo bo'lib tepaga suzadi (Vocab, layer 1)."""
    vocab_font = max(16, round(layout["font_size"] * 0.9))
    x = max(24, round(width * 0.04))
    base_y = round(height * 0.85)
    line_height = round(vocab_font * 1.5)
    distance = round(height * 0.75)             # ekranning ~75% masofasi
    target_y = base_y - distance
    duration_sec = 4.0
    speed = distance / duration_sec
    min_time_gap = line_height / speed          # so'zlar ustma-ust chiqmasin
    last_start = -999.0
    word_c = substyle.ass_inline("#FFFFFF")
    trans_c = substyle.ass_inline("#7DD3FC")    # ochiq ko'k tarjima
    dur_ms = int(duration_sec * 1000)
    exit_start, exit_end = dur_ms - 400, dur_ms
    for w in words:
        key = normalize_word(w.get("word", ""))
        tr = vocab_map.get(key, "") if key else ""
        if not tr:
            continue
        actual_start = max(float(w.get("start", 0.0)), last_start + min_time_gap)
        last_start = actual_start
        start = _format_ass_ts(actual_start)
        end = _format_ass_ts(actual_start + duration_sec)
        # Pop-in (xira+kichik -> tiniq+to'liq), tepaga suzish, oxirida pop-out
        override = (
            "{\\bord1\\shad1\\fad(300,400)\\move(%d,%d,%d,%d)"
            "\\blur3\\fscx50\\fscy50\\t(0,300,\\blur0\\fscx100\\fscy100)"
            "\\t(%d,%d,\\blur3\\fscx50\\fscy50)}"
        ) % (x, base_y, x, target_y, exit_start, exit_end)
        body = f"{override}{word_c}{_ass_text(key)} - {trans_c}{_ass_text(tr)}"
        f.write(f"Dialogue: 1,{start},{end},Vocab,,0,0,0,,{body}\n")


def cues_to_ass_dual_vocab(items: list[dict], words: list[dict],
                           vocab_map: dict[str, str], ass_path: str,
                           width: int, height: int, font: str,
                           layout: dict, style: dict) -> None:
    """Ikki qatlam subtitr (past) + ekranда aytilgan so'zlar lug'ati (chap,
    tepaga suzuvchi). items: [{start,end,orig,trans}], words: [{word,start,end}].
    """
    header = _ass_header(width, height, font, layout, style)
    # Default style'dan keyin, [Events] dan oldin Vocab uslubini qo'shamiz
    header = header.replace("\n\n[Events]",
                            "\n" + _vocab_style_line(font, layout) + "\n[Events]")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        _write_dual_events(f, items, layout, style)
        if words and vocab_map:
            _write_vocab_scroll(f, words, vocab_map, width, height, layout)
