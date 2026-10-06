"""Natija kartochkasi (sertifikat) rasmini yaratish — Pillow bo'lsa.

Pillow o'rnatilmagan bo'lsa yoki shrift topilmasa, make_result_card() None
qaytaradi va bot matnli natijaga tushadi (deploy'ni sindirmaydi).
"""
from __future__ import annotations

import io
import logging

log = logging.getLogger("quizcards")

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    _HAS_PIL = True
except Exception:  # Pillow yo'q
    _HAS_PIL = False

_FONT_CANDIDATES = [
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _font(size: int, bold: bool = False):
    cands = _FONT_BOLD_CANDIDATES if bold else _FONT_CANDIDATES
    for path in cands:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _grade(pct: int):
    if pct >= 90:
        return "A", (16, 163, 127)     # yashil
    if pct >= 70:
        return "B", (37, 99, 235)      # ko'k
    if pct >= 50:
        return "C", (217, 119, 6)      # to'q sariq
    return "D", (239, 68, 68)          # qizil


def _center(draw, text, font, cx, y, fill):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
    except Exception:
        w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def make_result_card(display_name: str, quiz_name: str, score: int,
                     total: int, pct: int):
    """Natija kartochkasi PNG baytlarini qaytaradi yoki None."""
    if not _HAS_PIL:
        return None
    try:
        W, H = 900, 560
        bg = (17, 17, 20)
        card = (26, 26, 32)
        muted = (150, 150, 165)
        white = (240, 240, 245)
        grade, accent = _grade(pct)

        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)

        # tashqi ramka / karta
        d.rounded_rectangle([30, 30, W - 30, H - 30], radius=28, fill=card,
                            outline=accent, width=3)
        # yuqori accent chiziq
        d.rounded_rectangle([30, 30, W - 30, 46], radius=8, fill=accent)

        cx = W // 2
        _center(d, "QUIZ NATIJASI", _font(26, True), cx, 78, muted)
        _center(d, display_name[:28], _font(46, True), cx, 118, white)
        _center(d, ("«" + quiz_name[:34] + "»"), _font(26), cx, 182, muted)

        # katta foiz doirasi
        ring_cx, ring_cy, R = cx, 320, 92
        d.ellipse([ring_cx - R, ring_cy - R, ring_cx + R, ring_cy + R],
                  outline=(55, 55, 66), width=14)
        # progress yoy (pieslice bilan taxminiy)
        end = -90 + (pct / 100) * 360
        d.arc([ring_cx - R, ring_cy - R, ring_cx + R, ring_cy + R],
              start=-90, end=end, fill=accent, width=14)
        _center(d, f"{pct}%", _font(56, True), ring_cx, ring_cy - 42, white)
        _center(d, f"{score}/{total}", _font(24), ring_cx, ring_cy + 26, muted)

        # baho beyji
        _center(d, f"Baho: {grade}", _font(32, True), cx, 438, accent)
        _center(d, "@tez_quizbot", _font(22), cx, 492, muted)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        log.exception("Natija kartochkasi yaratilmadi")
        return None
