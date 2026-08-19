"""Markdown matnidan akademik PDF yaratadi (reportlab, sof Python).

LibreOffice o'rniga — kam RAM serverda ham ishlaydi. Unicode (o', g', kirill)
uchun DejaVu/Liberation TTF shrifti ro'yxatdan o'tkaziladi.
Jadval, formula ($$...$$) va grafik (```chart JSON```) qo'llab-quvvatlanadi.
"""
from __future__ import annotations
import logging
import os
import re
import tempfile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, Image)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from docs.md_blocks import parse_blocks, strip_md

logger = logging.getLogger(__name__)

# Unicode TTF shrift nomzodlari (serif afzal — akademik ko'rinish)
_FONT_CANDIDATES = [
    ("Liberation Serif", "Liberation Serif Bold",
     "/usr/share/fonts/liberation-serif/LiberationSerif-Regular.ttf",
     "/usr/share/fonts/liberation-serif/LiberationSerif-Bold.ttf"),
    ("DejaVu Serif", "DejaVu Serif Bold",
     "/usr/share/fonts/dejavu-serif-fonts/DejaVuSerif.ttf",
     "/usr/share/fonts/dejavu-serif-fonts/DejaVuSerif-Bold.ttf"),
    ("DejaVu Sans", "DejaVu Sans Bold",
     "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
     "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"),
    ("Times New Roman", "Times New Roman Bold",
     r"C:\Windows\Fonts\times.ttf", r"C:\Windows\Fonts\timesbd.ttf"),
]

_FONT = "Helvetica"
_FONT_B = "Helvetica-Bold"
_registered = False


def _register_font() -> None:
    global _FONT, _FONT_B, _registered
    if _registered:
        return
    _registered = True
    for reg, bold, reg_path, bold_path in _FONT_CANDIDATES:
        if os.path.isfile(reg_path) and os.path.isfile(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(reg, reg_path))
                pdfmetrics.registerFont(TTFont(bold, bold_path))
                _FONT, _FONT_B = reg, bold
                return
            except Exception:
                continue


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _rich(text: str) -> str:
    """**qalin** ni <b> ga aylantiradi (reportlab mini-HTML)."""
    text = _esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text


def _latex_to_text(formula: str) -> str:
    """LaTeX ni o'qiladigan Unicode matnga aylantiradi (PDF uchun)."""
    if "\\" not in formula:
        return formula
    try:
        from pylatexenc.latex2text import LatexNodes2Text
        return LatexNodes2Text().latex_to_text(formula).strip() or formula
    except Exception:
        return formula


_MINISTRY = {
    "uz": "O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM, FAN VA INNOVATSIYALAR VAZIRLIGI",
    "ru": "МИНИСТЕРСТВО ВЫСШЕГО ОБРАЗОВАНИЯ, НАУКИ И ИННОВАЦИЙ РЕСПУБЛИКИ УЗБЕКИСТАН",
    "en": "MINISTRY OF HIGHER EDUCATION, SCIENCE AND INNOVATIONS OF THE REPUBLIC OF UZBEKISTAN",
}
_CITY = {"uz": "Toshkent", "ru": "Ташкент", "en": "Tashkent"}


def _title_page_flow(meta: dict, styles: dict) -> list:
    import datetime
    from reportlab.platypus import PageBreak
    lang = meta.get("language", "uz")
    c14 = styles["tc14"]
    c_big = styles["tc_big"]
    r14 = styles["tr14"]
    flow = [Paragraph("<b>" + _esc(_MINISTRY.get(lang, _MINISTRY["uz"])) + "</b>", styles["tc13"])]
    otm = (meta.get("otm") or "").strip()
    if otm:
        flow.append(Paragraph("<b>" + _esc(otm.upper()) + "</b>", c14))
    flow.append(Spacer(1, 70))
    fan = (meta.get("fan") or "").strip()
    if fan and fan != "—":
        flow.append(Paragraph(_esc(f"«{fan}» fanidan" if lang == "uz" else fan), c14))
    flow.append(Spacer(1, 20))
    flow.append(Paragraph("<b>" + _esc(meta.get("doc_label", "").upper()) + "</b>", c_big))
    topic = (meta.get("topic") or "").strip()
    t_label = {"uz": "Mavzu", "ru": "Тема", "en": "Topic"}.get(lang, "Mavzu")
    flow.append(Paragraph(f"<b>{_esc(t_label)}: {_esc(topic)}</b>", styles["tc16"]))
    flow.append(Spacer(1, 110))
    author = (meta.get("author") or "").strip()
    group = (meta.get("group") or "").strip()
    supervisor = (meta.get("supervisor") or "").strip()
    if author and author != "—":
        who = f"Bajardi: {author}" + (f" ({group})" if group and group != "—" else "")
        flow.append(Paragraph(_esc(who), r14))
    if supervisor and supervisor != "—":
        flow.append(Paragraph(_esc(f"Ilmiy rahbar: {supervisor}"), r14))
    flow.append(Spacer(1, 150))
    flow.append(Paragraph(
        "<b>" + _esc(f"{_CITY.get(lang, 'Toshkent')} — {datetime.date.today().year}") + "</b>",
        c14))
    flow.append(PageBreak())
    return flow


def build_pdf(markdown_text: str, output_path: str, title: str = "",
              meta: dict | None = None) -> str:
    _register_font()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=3 * cm, rightMargin=1.5 * cm,
    )
    usable_w = A4[0] - 4.5 * cm

    body = ParagraphStyle("body", fontName=_FONT, fontSize=14, leading=21,
                          alignment=TA_JUSTIFY, spaceAfter=6)
    h1 = ParagraphStyle("h1", fontName=_FONT_B, fontSize=16, leading=20,
                        alignment=TA_CENTER, spaceBefore=12, spaceAfter=8)
    h2 = ParagraphStyle("h2", fontName=_FONT_B, fontSize=15, leading=19,
                        alignment=TA_LEFT, spaceBefore=10, spaceAfter=6)
    h3 = ParagraphStyle("h3", fontName=_FONT_B, fontSize=14, leading=18,
                        alignment=TA_LEFT, spaceBefore=8, spaceAfter=5)
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=18, spaceAfter=3)
    formula = ParagraphStyle("formula", fontName=_FONT, fontSize=14, leading=20,
                             alignment=TA_CENTER, spaceBefore=6, spaceAfter=8)
    cell_style = ParagraphStyle("cell", fontName=_FONT, fontSize=11, leading=14)
    cell_head = ParagraphStyle("cellh", fontName=_FONT_B, fontSize=11, leading=14,
                               alignment=TA_CENTER)

    flow = []
    if meta:
        from reportlab.lib.enums import TA_RIGHT
        t_styles = {
            "tc13": ParagraphStyle("tc13", fontName=_FONT_B, fontSize=13, leading=17,
                                   alignment=TA_CENTER, spaceAfter=6),
            "tc14": ParagraphStyle("tc14", fontName=_FONT, fontSize=14, leading=18,
                                   alignment=TA_CENTER, spaceAfter=6),
            "tc16": ParagraphStyle("tc16", fontName=_FONT_B, fontSize=16, leading=21,
                                   alignment=TA_CENTER, spaceAfter=8),
            "tc_big": ParagraphStyle("tc_big", fontName=_FONT_B, fontSize=22, leading=28,
                                     alignment=TA_CENTER, spaceAfter=12),
            "tr14": ParagraphStyle("tr14", fontName=_FONT, fontSize=14, leading=20,
                                   alignment=TA_RIGHT, spaceAfter=4),
        }
        flow.extend(_title_page_flow(meta, t_styles))
    temp_files: list[str] = []
    num = 1

    for block in parse_blocks(markdown_text):
        kind = block[0]
        if kind == "h1":
            flow.append(Paragraph(_esc(block[1]).upper(), h1))
        elif kind == "h2":
            flow.append(Paragraph(_esc(block[1]), h2))
        elif kind == "h3":
            flow.append(Paragraph(_esc(block[1]), h3))
        elif kind == "bullet":
            flow.append(Paragraph("•&nbsp;" + _rich(block[1]), bullet))
        elif kind == "number":
            flow.append(Paragraph(f"{num}.&nbsp;" + _rich(block[1]), bullet))
            num += 1
            continue
        elif kind == "bold":
            flow.append(Paragraph("<b>" + _esc(block[1]) + "</b>", body))
        elif kind == "formula":
            flow.append(Paragraph("<i>" + _esc(_latex_to_text(block[1])) + "</i>", formula))
        elif kind == "table":
            rows = block[1]
            data = []
            for ri, row in enumerate(rows):
                data.append([Paragraph(_esc(strip_md(c)),
                                       cell_head if ri == 0 else cell_style)
                             for c in row])
            col_w = usable_w / len(rows[0])
            t = Table(data, colWidths=[col_w] * len(rows[0]), repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#64748b")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#deeaf6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            flow.append(Spacer(1, 4))
            flow.append(t)
            flow.append(Spacer(1, 6))
        elif kind == "chart":
            try:
                from docs.charts import render_chart
                fd, png = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                render_chart(block[1], png)
                temp_files.append(png)
                img_w = usable_w * 0.92
                flow.append(Spacer(1, 4))
                flow.append(Image(png, width=img_w, height=img_w * 880 / 1400))
                flow.append(Spacer(1, 4))
            except Exception as e:
                logger.warning("PDF grafik chizib bo'lmadi: %s", e)
        else:
            flow.append(Paragraph(_rich(block[1]), body))
        num = 1  # raqamli ro'yxat uzilsa qayta boshlanadi

    if not flow:
        flow.append(Paragraph(_esc(title or "Hujjat"), body))
    doc.build(flow)
    for f in temp_files:
        try:
            os.remove(f)
        except OSError:
            pass
    return output_path
