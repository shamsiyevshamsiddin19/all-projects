"""Reja fayllari — PostgreSQL bazada (BYTEA) saqlanadi."""

from __future__ import annotations

import os
import re
import secrets
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import Response
from sqlalchemy import text

from .. import db
from ..config import settings
from ..errors import ApiError, success
from ..owner import owner_context

ALLOWED_EXT = {
    "pdf", "doc", "docx",
    "jpg", "jpeg", "png", "gif", "webp", "bmp",
    "mp4", "webm", "mov", "avi", "mkv",
    "mp3", "ogg", "wav", "m4a",
}

MIME_MAP = {
    "pdf": "application/pdf", "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif",
    "webp": "image/webp", "bmp": "image/bmp",
    "mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime",
    "avi": "video/x-msvideo", "mkv": "video/x-matroska",
    "mp3": "audio/mpeg", "ogg": "audio/ogg", "wav": "audio/wav", "m4a": "audio/mp4",
}

_MIME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*$")


def _safe_mime(mime: str) -> str:
    mime = (mime or "").strip()
    return mime if _MIME_RE.match(mime) else "application/octet-stream"


def _type_from_ext(ext: str) -> str:
    if ext in {"jpg", "jpeg", "png", "gif", "webp", "bmp"}:
        return "image"
    if ext in {"mp4", "webm", "mov", "avi", "mkv"}:
        return "video"
    if ext in {"mp3", "ogg", "wav", "m4a"}:
        return "audio"
    if ext in {"pdf", "doc", "docx"}:
        return ext
    return "file"


def _format_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{round(n / 1024 / 1024, 1)} MB"
    if n >= 1024:
        return f"{round(n / 1024, 1)} KB"
    return f"{n} B"


def _content_disposition(mode: str, filename: str) -> str:
    mode = "attachment" if mode == "attachment" else "inline"
    name = os.path.basename(filename.replace("\\", "/")) or "file"
    ascii_name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip() or "file"
    ascii_name = re.sub(r'["\\\r\n]', "_", ascii_name)
    return f"{mode}; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"


async def upload(request: Request):
    form = await request.form()
    upload_file = form.get("file")
    if upload_file is None or not getattr(upload_file, "filename", None):
        raise ApiError("Fayl topilmadi.", 400)

    original = upload_file.filename
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in ALLOWED_EXT:
        raise ApiError(f"Bu turdagi fayl qo'llab-quvvatlanmaydi: .{ext}", 400)

    binary = await upload_file.read()
    file_size = len(binary)
    if file_size > settings.REJA_MAX_BYTES:
        raise ApiError(
            f"Fayl hajmi {_format_bytes(settings.REJA_MAX_BYTES)} dan oshmasligi kerak.", 400
        )

    ctx = owner_context(request)
    token = secrets.token_hex(32)
    mime_type = MIME_MAP.get(ext) or _safe_mime(upload_file.content_type or "")

    new_id = db.execute_returning_id(
        "INSERT INTO reja_files (owner_type, owner_key, access_token, original_name, mime_type, file_ext, "
        "file_size, file_data) VALUES (:ot, :ok, :tok, :on, :mt, :ext, :sz, :data)",
        {
            "ot": ctx["owner_type"], "ok": ctx["owner_key"], "tok": token, "on": original,
            "mt": mime_type, "ext": ext, "sz": file_size, "data": binary,
        },
    )

    url = f"/api?action=reja_file&id={new_id}&token={quote(token)}"
    return success({
        "id": new_id, "path": url, "url": url, "name": original,
        "type": _type_from_ext(ext), "size": file_size, "storage": "postgres",
    })


def serve(request: Request, file_id: int, token: str, download: bool):
    if file_id <= 0:
        raise ApiError("Fayl ID noto'g'ri.", 400)

    token = token.strip()
    if token != "" and not re.match(r"^[a-f0-9]{64}$", token, re.IGNORECASE):
        raise ApiError("Fayl token noto'g'ri.", 400)

    if token != "":
        row = db.fetch_one(
            "SELECT original_name, mime_type, file_size, file_data FROM reja_files "
            "WHERE id = :id AND access_token = :tok LIMIT 1",
            {"id": file_id, "tok": token},
        )
    else:
        # Token yo'q bo'lsa — faqat o'z egasi ko'ra oladi (begona enumeratsiya qila olmaydi).
        ctx = owner_context(request)
        row = db.fetch_one(
            "SELECT original_name, mime_type, file_size, file_data FROM reja_files "
            "WHERE id = :id AND owner_type = :ot AND owner_key = :ok LIMIT 1",
            {"id": file_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
        )

    if not row:
        raise ApiError("Fayl topilmadi.", 404)

    data = row["file_data"]
    if data is None:
        raise ApiError("Fayl bazadan o'qilmadi.", 500)
    if not isinstance(data, (bytes, bytearray)):
        data = bytes(data)

    disposition = "attachment" if download else "inline"
    return Response(
        content=bytes(data),
        media_type=_safe_mime(row.get("mime_type") or ""),
        headers={
            "Content-Disposition": _content_disposition(disposition, row.get("original_name") or "file"),
            "Cache-Control": "private, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )
