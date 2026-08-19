"""Subtitr uslubi (arxitektura 5.6) — foydalanuvchi sozlamasi -> ASS uslubi.

Foydalanuvchi Mini App'da rang/o'lcham/joylashuv tanlaydi, JSON sifatida
keladi. Bu modul uni tekshiradi (normalize) va ASS qiymatlariga aylantiradi.
Standart qiymatlar = avvalgi "toza kontur" (o'zgarmas xulq-atvor).

ASS rang formati: &HAABBGGRR (alpha, blue, green, red — hex).
"""
from __future__ import annotations

import re

DEFAULTS = {
    "text_color": "#FFFFFF",     # matn rangi (PrimaryColour)
    "outline_color": "#000000",  # kontur rangi (OutlineColour)
    "trans_color": "#FFE580",    # ikki qatlamда tarjima rangi (och sariq)
    "font_size": "medium",       # small / medium / large
    "position": "bottom",        # bottom / center / top
    "bold": True,
    "box": False,                # orqa fon qutisi
}

FONT_SCALE = {"small": 0.028, "medium": 0.033, "large": 0.040}
ALIGN = {"bottom": 2, "center": 5, "top": 8}

_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _is_hex(value) -> bool:
    return isinstance(value, str) and bool(_HEX_RE.match(value))


def normalize(raw) -> dict:
    """Kelgan (ishonchsiz) uslubni tekshirib, to'liq xavfsiz dict qaytaradi."""
    raw = raw if isinstance(raw, dict) else {}
    out = dict(DEFAULTS)
    for key in ("text_color", "outline_color", "trans_color"):
        if _is_hex(raw.get(key)):
            out[key] = "#" + raw[key].lstrip("#")
    if raw.get("font_size") in FONT_SCALE:
        out["font_size"] = raw["font_size"]
    if raw.get("position") in ALIGN:
        out["position"] = raw["position"]
    out["bold"] = bool(raw.get("bold", DEFAULTS["bold"]))
    out["box"] = bool(raw.get("box", DEFAULTS["box"]))
    return out


def font_scale(style: dict) -> float:
    return FONT_SCALE.get(style.get("font_size"), FONT_SCALE["medium"])


def alignment(style: dict) -> int:
    return ALIGN.get(style.get("position"), 2)


def ass_color(hexc: str, alpha: str = "00") -> str:
    """#RRGGBB -> &HAABBGGRR (ASS uslub qatori uchun)."""
    h = (hexc or "").lstrip("#")
    if len(h) != 6:
        h = "FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return ("&H" + alpha + b + g + r).upper()


def ass_inline(hexc: str) -> str:
    r"""#RRGGBB -> {\c&HBBGGRR&} (matn ichidagi rang override)."""
    h = (hexc or "").lstrip("#")
    if len(h) != 6:
        h = "FFFFFF"
    bgr = (h[4:6] + h[2:4] + h[0:2]).upper()
    return "{\\c&H" + bgr + "&}"
