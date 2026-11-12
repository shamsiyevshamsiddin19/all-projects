"""Hujjatlar: TXT, DOCX, o'qish uchun PDF va Yordamchi sayti uchun MD."""
from __future__ import annotations

import bisect
import csv
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .core import POS_ORDER, ReadingBlock, ReadingPair, Segment, _env_float, normalize_word, pos_label
from .media import seconds_to_srt_time
from .vocab import dedupe_by_lemma, is_translit_only
from .subtitles import FONTS_DIR

_pdf_font_ready = False


def write_txt_transcript(path: Path, original: list[Segment], translated: list[Segment] | None) -> None:
    lines: list[str] = ["MATN (1-format: Aralash)", "======================", ""]
    for i, seg in enumerate(original):
        lines.append(seg.text)
        if translated and i < len(translated):
            lines.append(f"    {translated[i].text}")
        lines.append("")

    if translated:
        lines += ["", "MATN (2-format: Alohida)", "========================", ""]
        lines += ["--- ORIGINAL ---", ""]
        for seg in original:
            lines.append(seg.text)

        lines += ["", "--- TARJIMA ---", ""]
        for seg in translated:
            lines.append(seg.text)

    path.write_text("\n".join(lines), encoding="utf-8-sig")


def _vocab_freq_note(e: dict[str, Any]) -> str:
    c = int(e.get("count", 1) or 1)
    return f"  (x{c})" if c > 1 else ""


def write_txt_vocab(path: Path, entries: list[dict[str, Any]]) -> None:
    # Bir xil o'zakli so'zlarni birlashtiramiz (kelgan/keldi -> kelmoq).
    merged = dedupe_by_lemma(entries)
    lines = ["LUG'AT (1-format: Chastota bo'yicha)", "=================================", ""]
    helpers = [e for e in merged if e.get("helper")]
    names = [e for e in merged if not e.get("helper") and is_translit_only(e)]
    main = [e for e in merged
            if not e.get("helper") and not is_translit_only(e)]
    lines.append(f"Asosiy so'zlar ({len(main)}) — eng ko'p uchraganlar tepada")
    lines.append("-" * 40)
    for e in main:
        lines.append(f"{e['word']} - {e['translation']}{_vocab_freq_note(e)}")
    if helpers:
        lines += ["", "Yordamchi so'zlar", "-" * 40]
        for e in helpers:
            lines.append(f"{e['word']} - {e['translation']} ({e['helper']}){_vocab_freq_note(e)}")
    if names:
        # Tarjimasi o'zi bilan bir xil — ism yoki o'zlashma.
        lines += ["", "Ismlar va o'zlashmalar", "-" * 40]
        for e in names:
            lines.append(f"{e['word']} - {e['translation']}{_vocab_freq_note(e)}")

    # Format 2
    lines += ["", "", "LUG'AT (2-format: So'z turkumlariga ajratilgan)", "===============================================", ""]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for e in merged:
        grouped.setdefault(pos_label(e), []).append(e)

    for cat in POS_ORDER:
        items = grouped.get(cat, [])
        if items:
            lines += [f"\n{cat} ({len(items)})", "-" * 40]
            for e in items:
                lines.append(f"{e['word']} - {e['translation']}{_vocab_freq_note(e)}")

    path.write_text("\n".join(lines), encoding="utf-8-sig")


def write_docx_transcript(path: Path, original: list[Segment], translated: list[Segment] | None) -> None:
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("DOCX uchun python-docx kerak: pip install python-docx") from exc
    doc = Document()
    doc.add_heading("Matn", level=1)
    for i, seg in enumerate(original):
        p = doc.add_paragraph()
        p.add_run(f"[{seconds_to_srt_time(seg.start)}] ").bold = True
        p.add_run(seg.text)
        if translated and i < len(translated):
            p2 = doc.add_paragraph(translated[i].text)
            p2.paragraph_format.left_indent = 240000
    doc.save(path)


def write_docx_vocab(path: Path, entries: list[dict[str, Any]]) -> None:
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("DOCX uchun python-docx kerak: pip install python-docx") from exc
    merged = dedupe_by_lemma(entries)
    doc = Document()
    doc.add_heading("Lug'at", level=1)
    table = doc.add_table(rows=1, cols=4)
    hdr = table.rows[0].cells
    hdr[0].text = "So'z"
    hdr[1].text = "Tarjima"
    hdr[2].text = "Turi"
    hdr[3].text = "Necha marta"
    for e in merged:
        row = table.add_row().cells
        row[0].text = str(e.get("word", ""))
        row[1].text = str(e.get("translation", ""))
        row[2].text = pos_label(e)
        row[3].text = str(int(e.get("count", 1) or 1))
    doc.save(path)


def write_csv_vocab(path: Path, entries: list[dict[str, Any]]) -> None:
    """Anki va Quizlet importi uchun sodda ustunli lug'at yozadi."""
    # Bitta lemma turli shakllarda takrorlansa, kartochkalar ham takrorlanib
    # ketadi va takrorlash navbati sun'iy uzayadi; shu sabab TXT/DOCX kabi
    # CSV ham birlashtirilgan ro'yxatdan tuziladi.
    merged = dedupe_by_lemma(entries)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["So'z", "Tarjima", "So'z turkumi", "Chastota"])
        for entry in merged:
            writer.writerow([
                str(entry.get("word", "")),
                str(entry.get("translation", "")),
                pos_label(entry),
                int(entry.get("count", 1) or 1),
            ])


def _read_find_font_set() -> tuple[Path, Path, Path, Path] | None:
    """Kirill harflari bor to'liq shrift to'rtligini topadi."""
    for names in _READ_PDF_FAMILIES:
        for directory in _READ_PDF_DIRS:
            try:
                if not directory.is_dir():
                    continue
            except OSError:
                continue
            found = [directory / n for n in names]
            if all(p.is_file() for p in found):
                return (found[0], found[1], found[2], found[3])
    return None


def _read_register_font() -> str:
    """PDF uchun shriftni ro'yxatdan o'tkazadi va oila nomini qaytaradi."""
    global _pdf_font_ready
    if _pdf_font_ready:
        return PDF_FONT
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "PDF uchun reportlab kerak: ilovada \"Paketlarni o'rnatish\" ni bosing "
            "yoki `pip install reportlab`"
        ) from exc
    found = _read_find_font_set()
    if not found:
        raise RuntimeError(
            "PDF uchun kirill harflari bor shrift topilmadi. O'rnating: "
            "`sudo apt install fonts-noto-serif` (Ubuntu) yoki shrift fayllarini "
            f"{FONTS_DIR} papkasiga qo'ying."
        )
    regular, bold, italic, bold_italic = found
    pdfmetrics.registerFont(TTFont(PDF_FONT, str(regular)))
    pdfmetrics.registerFont(TTFont(f"{PDF_FONT}-Bold", str(bold)))
    pdfmetrics.registerFont(TTFont(f"{PDF_FONT}-Italic", str(italic)))
    pdfmetrics.registerFont(TTFont(f"{PDF_FONT}-BoldItalic", str(bold_italic)))
    pdfmetrics.registerFontFamily(
        PDF_FONT,
        normal=PDF_FONT,
        bold=f"{PDF_FONT}-Bold",
        italic=f"{PDF_FONT}-Italic",
        boldItalic=f"{PDF_FONT}-BoldItalic",
    )
    _pdf_font_ready = True
    return PDF_FONT


def _read_pdf_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_pdf_reading(
    path: Path,
    title: str,
    blocks: list[ReadingBlock],
    meta: str = "",
    translated: list[ReadingBlock] | None = None,
    layout: str = "plain",
) -> None:
    """O'qish uchun A4 PDF yasaydi.

    Uchta maket:
      plain    — faqat original til (eng toza o'qish);
      parallel — har abzatsdan keyin tarjimasi (surilgan, kulrang);
      split    — avval butun original, keyin alohida bo'limda tarjimasi.
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate, Paragraph,
    )

    _read_register_font()
    body_pt = _env_float("SUBTITR_READ_FONT", 12.0)
    page_w, page_h = A4
    # Yon oqliqlar keng: qator ~70 belgi bo'ladi, bu uzun matnni o'qishga
    # eng qulay o'lcham.
    left = right = 2.8 * cm
    top = 2.4 * cm
    bottom = 2.2 * cm

    ink = colors.HexColor("#15171a")
    faint = colors.HexColor("#8b9099")

    style_title = ParagraphStyle(
        "ReadTitle", fontName=f"{PDF_FONT}-Bold", fontSize=body_pt + 8.5,
        leading=body_pt + 12.5, textColor=ink, spaceAfter=4, alignment=TA_LEFT,
    )
    style_meta = ParagraphStyle(
        "ReadMeta", fontName=f"{PDF_FONT}-Italic", fontSize=body_pt - 2.5,
        leading=body_pt, textColor=faint, alignment=TA_LEFT,
    )
    style_body = ParagraphStyle(
        "ReadBody", fontName=PDF_FONT, fontSize=body_pt,
        # 1.6 qator oralig'i — abzats zich bo'lmaydi, ko'z tez charchamaydi.
        leading=body_pt * 1.6, textColor=ink, alignment=TA_LEFT,
        spaceAfter=body_pt * 0.62,
        # Matn tekislanmaydi (ikki yoqqa cho'zilmaydi): rus tilida so'zlar
        # uzun, bo'g'in ko'chirish yo'q — tekislansa qatorlar orasida
        # oq "daryo"lar paydo bo'ladi.
        allowWidows=0, allowOrphans=0,
    )

    # Tarjima qatori: shrift o'lchami KICHRAYTIRILMAYDI (o'qiladigan matn
    # bo'lib qolsin) — farq surish va rang bilan beriladi.
    style_trans = ParagraphStyle(
        "ReadTrans", parent=style_body, textColor=colors.HexColor("#5b6472"),
        leftIndent=0.85 * cm, spaceBefore=1, spaceAfter=body_pt * 0.9,
    )
    style_section = ParagraphStyle(
        "ReadSection", fontName=f"{PDF_FONT}-Bold", fontSize=body_pt + 3,
        leading=body_pt + 7, textColor=ink, spaceAfter=body_pt * 1.2,
        alignment=TA_LEFT,
    )

    header = title if len(title) <= 72 else title[:71].rstrip() + "…"

    def draw_page(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont(PDF_FONT, body_pt - 2.5)
        canvas.setFillColor(faint)
        canvas.drawCentredString(page_w / 2, bottom * 0.52, str(canvas.getPageNumber()))
        if canvas.getPageNumber() > 1:
            # Kolontitul faqat ikkinchi sahifadan: birinchi sahifada
            # sarlavhaning o'zi turadi.
            canvas.drawRightString(page_w - right, page_h - top * 0.58, header)
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(path), pagesize=A4,
        leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom,
        title=title, author="Subtitr Desktop", subject="O'qish uchun matn",
    )
    frame = Frame(
        left, bottom, page_w - left - right, page_h - top - bottom,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="read",
    )
    doc.addPageTemplates([PageTemplate(id="read", frames=[frame], onPage=draw_page)])

    story: list[Any] = [Paragraph(_read_pdf_escape(title), style_title)]
    if meta:
        story.append(Paragraph(_read_pdf_escape(meta), style_meta))
    story.append(HRFlowable(
        width="100%", thickness=0.6, color=colors.HexColor("#d7dae0"),
        spaceBefore=11, spaceAfter=17,
    ))

    def body(block: ReadingBlock) -> Any:
        return Paragraph(_read_pdf_escape(block.text), style_body)

    if layout == "parallel" and translated:
        # Juftlik abzats bo'yicha: ikkala ro'yxat ham bir xil bo'laklardan
        # yig'ilgani uchun indekslari mos keladi.
        for i, block in enumerate(blocks):
            story.append(body(block))
            if i < len(translated):
                story.append(Paragraph(
                    _read_pdf_escape(translated[i].text), style_trans
                ))
    elif layout == "split" and translated:
        for block in blocks:
            story.append(body(block))
        story.append(PageBreak())
        story.append(Paragraph(_read_pdf_escape(SPLIT_HEADING), style_section))
        for block in translated:
            story.append(body(block))
    else:
        for block in blocks:
            story.append(body(block))
    if not blocks:
        story.append(Paragraph("Matn topilmadi.", style_body))
    doc.build(story)
