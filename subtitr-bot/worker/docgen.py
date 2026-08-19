"""Matn/lug'at natijalarini .txt va chiroyli .pdf ga yozish.

txt — UTF-8 BOM bilan (Windows'da belgilar buzilmaydi).
pdf — reportlab bilan: hoshiya (border), bot username suvbelgi (watermark),
sahifa raqami. Matn: bitta ustun (proza). Lug'at: ikki ustun + o'rtada chiziq,
keyin yordamchi so'zlar guruhlangan, so'ng so'z turkumlari bo'yicha.

DejaVu Sans (to'liq Unicode — o'zbek/kiril) ishlatiladi.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_FONT = "PdfSans"
_FONT_B = "PdfSans-Bold"
_registered = False

# Noto Sans afzal (subtitr bilan izchil, zamonaviy); bo'lmasa DejaVu zaxira
_REG_NAMES = ("NotoSans-Regular.ttf", "DejaVuSans.ttf")
_BOLD_NAMES = ("NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf")
_FONT_DIRS = ("/usr/share/fonts", "/usr/local/share/fonts")


def write_txt(path: str, text: str) -> None:
    """Matnni .txt faylga yozadi (UTF-8 BOM bilan)."""
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(text)


def _find_font(names: tuple[str, ...]) -> str | None:
    """Nomlarni ustuvorlik tartibida qidiradi (birinchi nom afzal)."""
    for n in names:
        for base in _FONT_DIRS:
            for root, _dirs, files in os.walk(base):
                if n in files:
                    return os.path.join(root, n)
    return None


def _ensure_fonts() -> None:
    global _registered
    if _registered:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    reg = _find_font(_REG_NAMES)
    bold = _find_font(_BOLD_NAMES)
    if reg:
        pdfmetrics.registerFont(TTFont(_FONT, reg))
    if bold:
        pdfmetrics.registerFont(TTFont(_FONT_B, bold))
    else:
        # bold topilmasa oddiy shriftни bold sifatida ishlatamiz
        if reg:
            pdfmetrics.registerFont(TTFont(_FONT_B, reg))
    _registered = True


# Sahifa o'lchamlari (barcha funksiyalar bir xil joylashuvni ishlatadi)
_BORDER_M = 1.0   # cm — tashqi hoshiya chetdan
_INSET = 0.7      # cm — matn hoshiyadan ichkarida
_FOOTER_H = 1.25  # cm — futer balandligi
_TITLE_H = 1.7    # cm — sarlavha uchun joy (1-sahifa)


def _content_box():
    """Matn joylashadigan ichki to'rtburchak: (x0, y0, kenglik, balandlik)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm

    w, h = A4
    x0 = (_BORDER_M + _INSET) * cm
    y0 = (_BORDER_M + _FOOTER_H) * cm
    width = w - 2 * (_BORDER_M + _INSET) * cm
    height = h - (_BORDER_M + _INSET) * cm - y0
    return x0, y0, width, height


def _decorations(brand: str, two_col: bool):
    """Har sahifaga: toza hoshiya, ko'rinadigan suvbelgi (bot username), futer."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm

    w, h = A4
    m = _BORDER_M * cm

    def on_page(canvas, doc):
        canvas.saveState()

        # Suvbelgi — bot username diagonal takrorlanadi (ENG ORQADA, ko'rinarli)
        if brand:
            canvas.saveState()
            canvas.setFont(_FONT_B, 26)
            canvas.setFillColor(colors.Color(0.45, 0.55, 0.72, alpha=0.07))
            canvas.translate(w / 2, h / 2)
            canvas.rotate(35)
            yy = -int(h)
            while yy < int(h):
                xx = -int(w)
                while xx < int(w):
                    canvas.drawCentredString(xx, yy, brand)
                    xx += 270
                yy += 120
            canvas.restoreState()

        # Tashqi hoshiya (zamonaviy yumaloq ramka)
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.setLineWidth(1.5)
        canvas.roundRect(m, m, w - 2 * m, h - 2 * m, 10, stroke=1, fill=0)

        # Ikki ustun orasidagi nuqtali chiziq
        if two_col:
            canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
            canvas.setLineWidth(0.6)
            canvas.setDash([2, 3])
            canvas.line(w / 2, (_BORDER_M + _FOOTER_H) * cm,
                        w / 2, h - (_BORDER_M + _INSET) * cm)
            canvas.setDash([])

        # Futer — ajratuvchi chiziq + brend va sahifa raqami
        canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
        canvas.setLineWidth(0.5)
        canvas.line(m + 0.3 * cm, _FOOTER_H * cm, w - m - 0.3 * cm, _FOOTER_H * cm)
        canvas.setFont(_FONT, 9)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        if brand:
            canvas.drawString(m + 0.3 * cm, _FOOTER_H * cm - 0.45 * cm, brand)
        canvas.drawRightString(
            w - m - 0.3 * cm, _FOOTER_H * cm - 0.45 * cm, f"{doc.page}-sahifa"
        )
        canvas.restoreState()

    return on_page


def _styles():
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle

    return {
        "title": ParagraphStyle(
            "title", fontName=_FONT_B, fontSize=20, leading=26,
            alignment=1, spaceAfter=20, textColor=colors.HexColor("#1E293B"),
        ),
        "section": ParagraphStyle(
            "section", fontName=_FONT_B, fontSize=14, leading=18,
            spaceBefore=14, spaceAfter=10, textColor=colors.HexColor("#2563EB"),
            borderPadding=4,
        ),
        "group": ParagraphStyle(
            "group", fontName=_FONT_B, fontSize=11, leading=16,
            spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#475569"),
        ),
        "entry": ParagraphStyle(
            "entry", fontName=_FONT, fontSize=10, leading=16,
            spaceAfter=3, textColor=colors.HexColor("#0F172A"),
        ),
        "body": ParagraphStyle(
            "body", fontName=_FONT, fontSize=11, leading=18,
            spaceAfter=8, textColor=colors.HexColor("#334155"),
        ),
    }


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_pdf_transcript(path: str, title: str, lines: list[str], brand: str = "") -> None:
    """Matn (transkript) PDF — bitta ustun, proza ko'rinishida."""
    _ensure_fonts()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph

    st = _styles()
    x0, y0, cw, ch = _content_box()
    frame = Frame(x0, y0, cw, ch, id="body", leftPadding=6, rightPadding=6,
                  topPadding=6, bottomPadding=4)
    doc = BaseDocTemplate(
        path, pagesize=A4, title=title or "Matn",
    )
    doc.addPageTemplates(
        PageTemplate(id="t", frames=[frame], onPage=_decorations(brand, two_col=False))
    )
    story = [Paragraph(_esc(title or "Videodagi matn"), st["title"])]
    for ln in lines:
        if ln.strip():
            story.append(Paragraph(_esc(ln), st["body"]))
    doc.build(story)


# Yordamchi so'z guruhlari (tartib bilan) va sarlavhalari
_HELPER_ORDER = [
    ("artikl", "Artikllar"),
    ("predlog", "Predloglar"),
    ("ko'makchi", "Ko'makchilar"),
    ("bog'lovchi", "Bog'lovchilar"),
    ("yuklama", "Yuklamalar"),
    ("modal", "Modal so'zlar"),
]
# So'z turkumlari (tartib bilan)
_POS_ORDER = [
    ("fe'l", "Fe'llar"),
    ("olmosh", "Olmoshlar"),
    ("ravish", "Ravishlar"),
]


def _norm(s: str) -> str:
    return (s or "").strip().lower().replace("’", "'").replace("ʻ", "'")


def write_pdf_vocab(path: str, title: str, entries: list[dict], brand: str = "") -> None:
    """Lug'at PDF — 2 ustun oqim + yordamchi so'zlar + so'z turkumlari bo'limlari.

    entries: [{"word","translation","pos","helper"}, ...] (paydo bo'lish tartibida).
    """
    _ensure_fonts()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak,
    )

    x0, y0, cw, ch = _content_box()
    gut = 0.7 * cm
    col_w = (cw - gut) / 2
    left = Frame(x0, y0, col_w, ch, id="L", leftPadding=4, rightPadding=8,
                 topPadding=6, bottomPadding=4)
    right = Frame(x0 + col_w + gut, y0, col_w, ch, id="R", leftPadding=8,
                  rightPadding=4, topPadding=6, bottomPadding=4)

    doc = BaseDocTemplate(
        path, pagesize=A4, title=title or "Lug'at",
    )
    doc.addPageTemplates(
        PageTemplate(id="2c", frames=[left, right], onPage=_decorations(brand, two_col=True))
    )
    st = _styles()

    def entry_para(e: dict):
        word = _esc(e.get("word", ""))
        tr = _esc(e.get("translation", ""))
        # Chiroyliroq chiziq va urg'u
        return Paragraph(
            f'<font color="#2563EB"><b>{word}</b></font> <font color="#CBD5E1">—</font> {tr}', st["entry"]
        )

    story = [Paragraph(_esc(title or "Lug'at — so'zlar va tarjimasi"), st["title"])]

    # 1-BO'LIM: asosiy lug'at (yordamchi bo'lmagan so'zlar), paydo bo'lish tartibida
    content = [e for e in entries if _norm(e.get("helper")) in ("", "yo'q", "yoq", "none")]
    story.append(Paragraph(f"Lug'at ({len(content)} so'z)", st["section"]))
    for e in content:
        story.append(entry_para(e))

    # 2-BO'LIM: yordamchi so'zlar — guruhlangan (yangi sahifadan)
    helpers = [e for e in entries if _norm(e.get("helper")) not in ("", "yo'q", "yoq", "none")]
    if helpers:
        story.append(PageBreak())
        story.append(Paragraph("Yordamchi so'zlar", st["section"]))
        used = set()
        for key, label in _HELPER_ORDER:
            grp = [e for e in helpers if _norm(e.get("helper")) == key]
            if not grp:
                continue
            used.update(id(e) for e in grp)
            story.append(Paragraph(label, st["group"]))
            for e in grp:
                story.append(entry_para(e))
        other = [e for e in helpers if id(e) not in used]
        if other:
            story.append(Paragraph("Boshqa yordamchilar", st["group"]))
            for e in other:
                story.append(entry_para(e))

    # 3-BO'LIM: so'z turkumlari bo'yicha hamma so'zlar (yangi sahifadan).
    # Samarali turkum = yordamchi toifa (bo'lsa) yoki so'z turkumi.
    if entries:
        story.append(PageBreak())
        story.append(Paragraph("So'z turkumlari bo'yicha", st["section"]))

        def cat_of(e):
            return _norm(e.get("helper")) if _norm(e.get("helper")) not in (
                "", "yo'q", "yoq", "none") else _norm(e.get("pos"))

        order = _POS_ORDER + [(k, lbl) for k, lbl in _HELPER_ORDER]
        used = set()
        for key, label in order:
            grp = [e for e in entries if cat_of(e) == key]
            if not grp:
                continue
            used.update(id(e) for e in grp)
            story.append(Paragraph(label, st["group"]))
            for e in grp:
                story.append(entry_para(e))
        other = [e for e in entries if id(e) not in used]
        if other:
            story.append(Paragraph("Boshqa", st["group"]))
            for e in other:
                story.append(entry_para(e))

    doc.build(story)


def _is_helper(e: dict) -> bool:
    return _norm(e.get("helper")) not in ("", "yo'q", "yoq", "none")


def write_txt_vocab(path: str, title: str, entries: list[dict]) -> None:
    """Sektsiyalangan lug'at .txt — PDF bilan bir xil tuzilma (UTF-8 BOM).

    Bo'limlar: asosiy lug'at + yordamchi so'zlar (guruhlangan) + so'z turkumlari.
    """
    def fmt(e: dict) -> str:
        return f"{e.get('word', '')} — {e.get('translation', '')}"

    out: list[str] = [title, "=" * max(8, len(title)), ""]

    # 1) Asosiy lug'at (yordamchi bo'lmaganlar, paydo bo'lish tartibida)
    content = [e for e in entries if not _is_helper(e)]
    out.append(f"📖 LUG'AT ({len(content)} so'z)")
    out.append("-" * 30)
    out += [fmt(e) for e in content]

    # 2) Yordamchi so'zlar — guruhlangan
    helpers = [e for e in entries if _is_helper(e)]
    if helpers:
        out += ["", "", "🔧 YORDAMCHI SO'ZLAR", "-" * 30]
        used = set()
        for key, label in _HELPER_ORDER:
            grp = [e for e in helpers if _norm(e.get("helper")) == key]
            if not grp:
                continue
            used.update(id(e) for e in grp)
            out += ["", f"• {label}:"]
            out += [f"  {fmt(e)}" for e in grp]
        other = [e for e in helpers if id(e) not in used]
        if other:
            out += ["", "• Boshqa yordamchilar:"]
            out += [f"  {fmt(e)}" for e in other]

    # 3) So'z turkumlari bo'yicha
    if entries:
        out += ["", "", "🏷 SO'Z TURKUMLARI BO'YICHA", "-" * 30]

        def cat_of(e: dict) -> str:
            h = _norm(e.get("helper"))
            return h if h not in ("", "yo'q", "yoq", "none") else _norm(e.get("pos"))

        used = set()
        for key, label in _POS_ORDER + _HELPER_ORDER:
            grp = [e for e in entries if cat_of(e) == key]
            if not grp:
                continue
            used.update(id(e) for e in grp)
            out += ["", f"• {label}:"]
            out += [f"  {fmt(e)}" for e in grp]
        other = [e for e in entries if id(e) not in used]
        if other:
            out += ["", "• Boshqa:"]
            out += [f"  {fmt(e)}" for e in other]

    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(out))
