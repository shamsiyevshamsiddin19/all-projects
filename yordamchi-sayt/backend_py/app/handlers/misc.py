"""Turli endpoint'lar: health, log_client, save_app_icon."""

from __future__ import annotations

import base64
import io
import json
import logging
import re
import time
from urllib.parse import quote

from fastapi import Request

from .. import db
from ..config import settings
from ..errors import ApiError, success
from .common import s

logger = logging.getLogger("yordamchi")

HEALTH_TABLES = [
    "app_storage", "reja_files", "quiz_bases", "quiz_questions", "quiz_progress",
    "goals", "goal_folders", "goal_sections", "dictionary_words", "dictionary_mistakes",
    "sport_exercises", "users", "user_channels", "plans", "history", "settings", "sent_logs",
    "activity_log",
]


def _clip(value, limit: int) -> str:
    # Yangi qatorlarni bo'shliqqa aylantirib, uzunlikni cheklaymiz (log-injection/log-fill himoyasi).
    text = s(value).replace("\r", " ").replace("\n", " ")
    return text[:limit]


# Faqat ma'lum log darajalari (aks holda mijoz istalgan logging atributini chaqira olardi).
_ALLOWED_LOG_LEVELS = {"debug", "info", "warning", "error", "critical"}


def log_client(request: Request, body: dict):
    level = s(body.get("level")).lower() or "info"
    if level not in _ALLOWED_LOG_LEVELS:
        level = "info"
    message = _clip(body.get("message"), 1000) or "Frontend log"
    logger.log(
        getattr(logging, level.upper(), logging.INFO),
        "CLIENT: %s | page=%s url=%s",
        message, _clip(body.get("page"), 200), _clip(body.get("url"), 300),
    )
    return success()


def _table_count(table: str) -> int | None:
    if not re.match(r"^[A-Za-z0-9_]+$", table):
        return None
    exists = db.fetch_value(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = current_schema() AND table_name = :t",
        {"t": table},
    )
    if not exists or int(exists) <= 0:
        return None
    # table nomi yuqorida qat'iy regex bilan tekshirilgan (injection'siz).
    return int(db.fetch_value(f'SELECT COUNT(*) FROM "{table}"') or 0)


def health(request: Request, body: dict):
    import sys

    # Baza host/port/nomi kabi ma'lumotlar faqat DEBUG rejimida ochiladi (ochiq endpoint).
    db_info: dict = {"connected": False, "error": None}
    if settings.DEBUG:
        db_info.update({"host": settings.DB_HOST, "port": settings.DB_PORT, "database": settings.DB_NAME})

    payload = {
        "success": True,
        "app": "yordamchi",
        "runtime": {"python": sys.version.split()[0], "framework": "fastapi"},
        "db": db_info,
        "tables": {},
    }
    try:
        db.fetch_value("SELECT 1")
        db_info["connected"] = True
        for t in HEALTH_TABLES:
            payload["tables"][t] = _table_count(t)
    except Exception as e:  # noqa: BLE001
        payload["success"] = False
        db_info["error"] = str(e) if settings.DEBUG else "connection error"
        logger.exception("Health tekshiruvda baza xatosi")
    return success(payload)


# --- App ikonka saqlash -----------------------------------------------------

def save_app_icon(request: Request, body: dict):
    data_url = s(body.get("icon"))
    if data_url == "":
        raise ApiError("Icon rasmi yuborilmadi.", 400)
    if not re.match(r"^data:image/(png|jpeg|jpg|webp);base64,", data_url, re.IGNORECASE):
        raise ApiError("Icon formati noto'g'ri. PNG, JPG yoki WebP rasm yuboring.", 400)

    raw = re.sub(r"^data:image/[^;]+;base64,", "", data_url, flags=re.IGNORECASE)
    try:
        binary = base64.b64decode(raw, validate=True)
    except Exception:
        raise ApiError("Icon rasmini o'qib bo'lmadi.", 400)

    if len(binary) < 128:
        raise ApiError("Icon rasmini o'qib bo'lmadi.", 400)
    if len(binary) > settings.ICON_MAX_BYTES:
        raise ApiError("Icon hajmi 2MB dan oshmasligi kerak.", 400)

    png_192 = _render_icon(binary, 192)
    png_512 = _render_icon(binary, 512)
    if png_192 is None:
        raise ApiError("Yaroqli rasm topilmadi.", 400)
    if png_512 is None:
        png_512 = png_192

    icon_dir = settings.ICON_DIR
    icon_dir.mkdir(parents=True, exist_ok=True)
    (icon_dir / "custom-app-icon-192.png").write_bytes(png_192)
    (icon_dir / "custom-app-icon-512.png").write_bytes(png_512)

    version = str(int(time.time()))
    if not _update_manifest_version(version):
        raise ApiError("Icon saqlandi, lekin manifest faylini yangilab bo'lmadi.", 500)

    return success({
        "icon_192": f"assets/icons/custom-app-icon-192.png?v={version}",
        "icon_512": f"assets/icons/custom-app-icon-512.png?v={version}",
        "version": version,
    })


def _render_icon(binary: bytes, size: int) -> bytes | None:
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow o'rnatilmagan — ikonka o'lchamsiz saqlanadi.")
        return binary
    try:
        src = Image.open(io.BytesIO(binary)).convert("RGBA")
    except Exception:
        return None
    w, h = src.size
    side = max(1, min(w, h))
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = src.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    out = io.BytesIO()
    cropped.save(out, format="PNG")
    return out.getvalue()


def _update_manifest_version(version: str) -> bool:
    path = settings.MANIFEST_FILE
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(manifest, dict):
        return False
    safe_version = quote(version, safe="")
    for icon in manifest.get("icons", []):
        if isinstance(icon, dict) and "src" in icon:
            base = icon["src"].split("?", 1)[0]
            if "custom-app-icon" in base:
                icon["src"] = f"{base}?v={safe_version}"
    try:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False
