"""Oddiy akademik diagrammalar — Pillow bilan (matplotlib'siz, kam RAM).

AI dan keladigan spec:
  {"type": "bar"|"line"|"pie", "title": "...", "labels": [...], "values": [...],
   "ylabel": "..." (ixtiyoriy)}
"""
from __future__ import annotations
import math
import os
from PIL import Image, ImageDraw, ImageFont

_W, _H = 1400, 880
_BG = (255, 255, 255)
_FG = (30, 41, 59)
_GRID = (203, 213, 225)
_AXIS = (100, 116, 139)
_PALETTE = [
    (46, 94, 140), (14, 124, 94), (192, 92, 46), (124, 58, 237),
    (185, 28, 28), (3, 105, 161), (161, 98, 7), (15, 118, 110),
]

_FONT_PATHS = [
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_FONT_BOLD_PATHS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for p in (_FONT_BOLD_PATHS if bold else _FONT_PATHS):
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _tw(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    return int(draw.textlength(text, font=font))


def _fmt(v: float) -> str:
    if float(v) == int(v):
        return str(int(v))
    return f"{v:.1f}"


def _nice_max(v: float) -> float:
    """Y o'qi uchun 'chiroyli' maksimum (5 ga bo'linadigan)."""
    if v <= 0:
        return 5.0
    mag = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * mag:
            return m * mag
    return 10 * mag


def _validate(spec: dict) -> tuple[str, str, list[str], list[float]]:
    ctype = str(spec.get("type", "bar")).lower()
    title = str(spec.get("title", "")).strip()
    labels = [str(x)[:18] for x in spec.get("labels", [])]
    values = [float(x) for x in spec.get("values", [])]
    n = min(len(labels), len(values), 12)
    if n < 2:
        raise ValueError("chart: kamida 2 ta label/value kerak")
    return ctype, title, labels[:n], values[:n]


def render_chart(spec: dict, out_path: str) -> str:
    ctype, title, labels, values = _validate(spec)
    img = Image.new("RGB", (_W, _H), _BG)
    draw = ImageDraw.Draw(img)

    f_title = _font(40, bold=True)
    if title:
        draw.text(((_W - _tw(draw, title, f_title)) // 2, 24), title,
                  fill=_FG, font=f_title)

    if ctype == "pie":
        _pie(draw, labels, values)
    elif ctype == "line":
        _axes_chart(draw, labels, values, spec.get("ylabel", ""), line=True)
    else:
        _axes_chart(draw, labels, values, spec.get("ylabel", ""), line=False)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


def _axes_chart(draw, labels, values, ylabel: str, line: bool):
    f_tick = _font(26)
    f_val = _font(26, bold=True)
    left, right, top, bottom = 130, 50, 110, 150
    px, py = left, top
    pw, ph = _W - left - right, _H - top - bottom

    vmax = _nice_max(max(values))
    vmin = min(0.0, min(values))
    span = vmax - vmin or 1.0

    # Gorizontal to'r chiziqlari + Y belgilar
    steps = 5
    for i in range(steps + 1):
        v = vmin + span * i / steps
        y = py + ph - int(ph * (v - vmin) / span)
        draw.line([(px, y), (px + pw, y)], fill=_GRID, width=2)
        t = _fmt(v)
        draw.text((px - _tw(draw, t, f_tick) - 12, y - 14), t, fill=_AXIS, font=f_tick)

    # O'qlar
    zero_y = py + ph - int(ph * (0 - vmin) / span)
    draw.line([(px, py), (px, py + ph)], fill=_AXIS, width=3)
    draw.line([(px, zero_y), (px + pw, zero_y)], fill=_AXIS, width=3)
    if ylabel:
        draw.text((px, py - 40), str(ylabel)[:30], fill=_AXIS, font=f_tick)

    n = len(values)
    slot = pw / n

    if line:
        pts = []
        for i, v in enumerate(values):
            x = px + int(slot * (i + 0.5))
            y = py + ph - int(ph * (v - vmin) / span)
            pts.append((x, y))
        draw.line(pts, fill=_PALETTE[0], width=5, joint="curve")
        for (x, y), v in zip(pts, values):
            draw.ellipse([x - 8, y - 8, x + 8, y + 8], fill=_PALETTE[0], outline=_BG, width=2)
            t = _fmt(v)
            draw.text((x - _tw(draw, t, f_val) // 2, y - 44), t, fill=_FG, font=f_val)
    else:
        bw = int(slot * 0.58)
        for i, v in enumerate(values):
            x0 = px + int(slot * i + (slot - bw) / 2)
            y1 = py + ph - int(ph * (v - vmin) / span)
            color = _PALETTE[i % len(_PALETTE)] if n <= len(_PALETTE) else _PALETTE[0]
            draw.rectangle([x0, min(y1, zero_y), x0 + bw, max(y1, zero_y)], fill=color)
            t = _fmt(v)
            draw.text((x0 + bw // 2 - _tw(draw, t, f_val) // 2, min(y1, zero_y) - 38),
                      t, fill=_FG, font=f_val)

    # X belgilar (uzunlarini ikki qatorli qilib bo'lish)
    for i, lab in enumerate(labels):
        cx = px + int(slot * (i + 0.5))
        if _tw(draw, lab, f_tick) > slot - 8 and " " in lab:
            mid = len(lab) // 2
            sp = lab.rfind(" ", 0, mid + 3)
            sp = sp if sp > 0 else lab.find(" ")
            l1, l2 = lab[:sp], lab[sp + 1:]
            draw.text((cx - _tw(draw, l1, f_tick) // 2, py + ph + 14), l1, fill=_FG, font=f_tick)
            draw.text((cx - _tw(draw, l2, f_tick) // 2, py + ph + 46), l2, fill=_FG, font=f_tick)
        else:
            draw.text((cx - _tw(draw, lab, f_tick) // 2, py + ph + 14), lab, fill=_FG, font=f_tick)


def _pie(draw, labels, values):
    f_leg = _font(28)
    f_pct = _font(26, bold=True)
    total = sum(abs(v) for v in values) or 1.0
    cx, cy, r = 400, 470, 300
    box = [cx - r, cy - r, cx + r, cy + r]

    ang = -90.0
    for i, v in enumerate(values):
        frac = abs(v) / total
        end = ang + 360.0 * frac
        color = _PALETTE[i % len(_PALETTE)]
        draw.pieslice(box, ang, end, fill=color, outline=_BG, width=3)
        # foiz belgisi bo'lak o'rtasida (juda kichkina bo'laklarda tashqarida)
        mid = math.radians((ang + end) / 2)
        dist = r * 0.62 if frac >= 0.07 else r * 1.15
        tx = cx + int(dist * math.cos(mid))
        ty = cy + int(dist * math.sin(mid))
        pct = f"{frac * 100:.0f}%"
        fill = _BG if frac >= 0.07 else _FG
        draw.text((tx - _tw(draw, pct, f_pct) // 2, ty - 14), pct, fill=fill, font=f_pct)
        ang = end

    # Legenda (o'ng tomonda)
    lx, ly = 800, 200
    for i, (lab, v) in enumerate(zip(labels, values)):
        color = _PALETTE[i % len(_PALETTE)]
        y = ly + i * 52
        draw.rectangle([lx, y, lx + 34, y + 34], fill=color)
        draw.text((lx + 48, y + 2), f"{lab} — {_fmt(v)}", fill=_FG, font=f_leg)
