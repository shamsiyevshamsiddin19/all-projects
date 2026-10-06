"""Umumiy yordamchilar: matn tozalash, vaqt formatlash, hajm."""
from __future__ import annotations

import html as _html
import re
from datetime import datetime, timedelta

# Telegram bot orqali yuboriladigan fayl maksimal hajmi (~50 MB)
TG_FILE_LIMIT = 50 * 1024 * 1024

_WS = re.compile(r"\s+")


def clean(text: str | None) -> str:
    """HTML entitilarni ochib, ortiqcha bo'shliqlarni yig'ish."""
    if not text:
        return ""
    return _WS.sub(" ", _html.unescape(text)).strip()


def esc(text: str | None) -> str:
    """HTML parse_mode uchun xavfsiz qilish."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def human_size(n: int) -> str:
    f = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if f < 1024 or unit == "GB":
            return f"{f:.0f} {unit}" if unit == "B" else f"{f:.1f} {unit}"
        f /= 1024
    return f"{f:.1f} GB"


def fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


def time_left(dt: datetime | None, now: datetime | None = None) -> str:
    """Deadline'gacha qolgan vaqtni o'zbekcha."""
    if not dt:
        return "—"
    now = now or datetime.now(dt.tzinfo)
    delta = dt - now
    if delta.total_seconds() <= 0:
        return "muddati o'tgan"
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append(f"{days} kun")
    if hours:
        parts.append(f"{hours} soat")
    if minutes and not days:
        parts.append(f"{minutes} daqiqa")
    return " ".join(parts) or "1 daqiqadan kam"


def parse_lms_deadline(text: str, tz=None) -> datetime | None:
    """'27-02-2026 23:59:59' -> datetime."""
    text = clean(text)
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{2}):(\d{2}):(\d{2})", text)
    if not m:
        m2 = re.search(r"(\d{2})-(\d{2})-(\d{4})", text)
        if not m2:
            return None
        d, mo, y = map(int, m2.groups())
        dt = datetime(y, mo, d, 23, 59, 59)
    else:
        d, mo, y, hh, mm, ss = map(int, m.groups())
        dt = datetime(y, mo, d, hh, mm, ss)
    return dt.replace(tzinfo=tz) if tz else dt
