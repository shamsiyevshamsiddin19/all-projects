"""Xatoliklar va JSON javob yordamchilari.

PHP versiyasida `api_error('...' . $e->getMessage())` xatolik tafsilotini (SQL, baza
tuzilishi) to'g'ridan-to'g'ri foydalanuvchiga qaytarardi. Bu versiyada tafsilot faqat
log'ga yoziladi; foydalanuvchiga umumiy xabar boradi (DEBUG=on bo'lganda bundan mustasno).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("yordamchi")


class ApiError(Exception):
    """Nazorat ostidagi xatolik — foydalanuvchiga ko'rsatish xavfsiz."""

    def __init__(self, message: str, status: int = 400, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.payload = payload or {}


class AuthError(Exception):
    """Auth (holat/xabar) formatidagi xatolik."""

    def __init__(self, message: str, status: int = 200, extra: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.extra = extra or {}


def json_response(payload: dict[str, Any], status: int = 200) -> JSONResponse:
    # PHP JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES ekvivalenti.
    content = json.dumps(payload, ensure_ascii=False)
    return JSONResponse(
        content=json.loads(content),
        status_code=status,
        media_type="application/json; charset=UTF-8",
    )


def success(payload: dict[str, Any] | None = None, status: int = 200) -> JSONResponse:
    body = {"success": True}
    if payload:
        body.update(payload)
    return json_response(body, status)


def error(message: str, status: int = 400, payload: dict[str, Any] | None = None) -> JSONResponse:
    body = {"success": False, "error": str(message)}
    if payload:
        body.update(payload)
    return json_response(body, status)


def auth_response(holat: bool, xabar: str, extra: dict[str, Any] | None = None, status: int = 200) -> JSONResponse:
    body = {"holat": bool(holat), "xabar": str(xabar)}
    if extra:
        body.update(extra)
    return json_response(body, status)


def register_exception_handlers(app) -> None:
    from .config import settings

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return error(exc.message, exc.status, exc.payload)

    @app.exception_handler(AuthError)
    async def _auth_error(_: Request, exc: AuthError):
        return auth_response(False, exc.message, exc.extra, exc.status)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # To'liq tafsilotni faqat log'ga yozamiz.
        logger.exception("Kutilmagan server xatosi: %s %s", request.method, request.url.path)
        if settings.DEBUG:
            return error(f"Server xatosi: {exc}", 500)
        return error("Server xatosi. Iltimos keyinroq urinib ko'ring.", 500)
