"""Test muhiti.

`app.config` modul darajasida `get_settings()` ni chaqiradi va
`SESSION_SECRET` bo'lmasa `RuntimeError` tashlaydi (bu ATAYLAB shunday —
ishlab chiqarishda sirsiz ishga tushmasligi kerak). Shuning uchun muhit
o'zgaruvchilari `app` import qilinishidan OLDIN qo'yilishi shart.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# backend_py/ ni import yo'liga qo'shamiz (`app` paketi shu yerda).
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# DIQQAT: bu qiymatlar `app` importidan OLDIN qo'yilishi kerak.
os.environ.setdefault("SESSION_SECRET", "test-faqat-sinov-uchun-haqiqiy-sir-emas")
os.environ.setdefault("ALLOWED_EMAILS", "admin@example.com")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("REQUIRE_AUTH", "true")
os.environ.setdefault("AUTH_MODE", "google")
# Testlar bazaga ulanmaydi — ulanish satri faqat Settings to'lishi uchun.
os.environ.setdefault("DB_NAME", "yordamchi_test")
# Log papkasi loyihadan tashqarida bo'lsin (test artefakt qoldirmasin).
os.environ.setdefault("LOG_DIR", str(BACKEND_ROOT / ".local-logs"))

import pytest
from starlette.requests import Request


def make_request(
    session: dict | None = None,
    headers: dict[str, str] | None = None,
    path: str = "/api",
    query: str = "action=delete_db",
    client_host: str = "203.0.113.9",
) -> Request:
    """Haqiqiy HTTP so'rovsiz `Request` yasaydi.

    `request.session` — `SessionMiddleware` qo'yadigan `scope["session"]`
    lug'ati. Shuning uchun uni to'g'ridan-to'g'ri berish mumkin va
    ruxsat tekshiruvini bazasiz, tarmoqsiz sinash mumkin bo'ladi.
    """
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": query.encode(),
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ],
        "client": (client_host, 54321),
        "server": ("y.wstore.uz", 443),
        "session": session if session is not None else {},
    }
    return Request(scope)


@pytest.fixture
def admin_request() -> Request:
    """`.env` dagi ALLOWED_EMAILS ro'yxatidagi egasi."""
    return make_request({"doktor_id": 1, "doktor_email": "admin@example.com", "role": "user"})


@pytest.fixture
def user_request() -> Request:
    """Admin qo'shgan oddiy foydalanuvchi — kirgan, lekin egasi EMAS."""
    return make_request({"doktor_id": 7, "doktor_email": "oddiy@example.com", "role": "user"})


@pytest.fixture
def anon_request() -> Request:
    """Tizimga kirmagan."""
    return make_request({})
