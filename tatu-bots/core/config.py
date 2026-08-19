"""Sozlamalar — .env dan o'qiladi."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _ids(raw: str) -> set[int]:
    out = set()
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out


def _ints(raw: str, default: list[int]) -> list[int]:
    out = []
    for part in (raw or "").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            out.append(int(part))
    return out or default


@dataclass
class Settings:
    lms_bot_token: str = os.getenv("LMS_BOT_TOKEN", "")
    hemis_bot_token: str = os.getenv("HEMIS_BOT_TOKEN", "")
    fernet_key: str = os.getenv("FERNET_KEY", "")
    lms_base_url: str = os.getenv("LMS_BASE_URL", "https://lms.tuit.uz").rstrip("/")
    hemis_base_url: str = os.getenv("HEMIS_BASE_URL", "").rstrip("/")
    db_path: str = os.getenv("DB_PATH", "tatu.db")
    tz: str = os.getenv("TZ", "Asia/Tashkent")
    morning_push: str = os.getenv("MORNING_PUSH", "07:00")
    admin_ids: set[int] = field(default_factory=lambda: _ids(os.getenv("ADMIN_IDS", "")))
    deadline_reminders: list[int] = field(
        default_factory=lambda: _ints(os.getenv("DEADLINE_REMINDERS", ""), [1440, 180, 30, 5])
    )
    test_login: str = os.getenv("TEST_LOGIN", "")
    test_password: str = os.getenv("TEST_PASSWORD", "")
    # Admin panel (web)
    web_host: str = os.getenv("WEB_HOST", "127.0.0.1")
    web_port: int = int(os.getenv("WEB_PORT", "8093"))
    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "2501")
    bridge_secret: str = os.getenv("TATULMS_BRIDGE_SECRET", "")

    @property
    def db_file(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else BASE_DIR / p


settings = Settings()
