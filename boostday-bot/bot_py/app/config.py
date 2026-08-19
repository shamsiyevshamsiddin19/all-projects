"""Bot konfiguratsiyasi — barcha sirlar muhit o'zgaruvchilaridan (.env) o'qiladi.

Kodda hech qanday token/parol/ID qattiq yozilmagan: hammasi `.env` orqali
beriladi (namuna uchun `.env.example` ga qarang). DB_* qiymatlari saytning
`Yordamchisayt/backend_py/.env` dagi DB_* bilan bir xil bo'lishi kerak —
ikkalasi bitta PostgreSQL bazasidan foydalanadi.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

APP_ROOT = Path(__file__).resolve().parent.parent  # bot_py/


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _admin_ids() -> list[int]:
    raw = os.getenv("BOT_ADMIN_IDS", "").strip()
    if not raw:
        return []
    out = []
    for part in raw.replace(",", " ").split():
        try:
            out.append(int(part))
        except ValueError:
            continue
    return out


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "boostdaybot")
    BOT_ID: int = _int("BOT_ID", 0)
    ADMIN_IDS: list[int] = _admin_ids()
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    # Sayt (y.wstore.uz) initData'siz murojaat qilganda talab qilinadigan maxfiy kalit.
    # Bo'sh bo'lsa — initData'siz murojaat UMUMAN qabul qilinmaydi (xavfsiz default).
    SITE_SECRET: str = os.getenv("SITE_SECRET", "")
    WEB_APP_URL: str = os.getenv("WEB_APP_URL", "")
    # Per-user Telegram Mini App manzili (bot tugmasi va menu shu yerni ochadi).
    MINIAPP_URL: str = os.getenv("MINIAPP_URL", "https://y.wstore.uz/boost/app")

    # --- Web Push (VAPID) ---
    # Telefondagi haqiqiy bildirishnoma uchun. OCHIQ kalit brauzerga
    # beriladi, MAXFIY kalit faqat serverda qoladi.
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_SUBJECT: str = os.getenv("VAPID_SUBJECT", "")

    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tashkent")

    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = _int("DB_PORT", 5432)
    DB_NAME: str = os.getenv("DB_NAME", "yordamchi")
    DB_USER: str = os.getenv("DB_USER", "yordamchi")
    DB_PASS: str = os.getenv("DB_PASS", "")
    DB_POOL_SIZE: int = _int("DB_POOL_SIZE", 5)

    LOG_FILE: str = os.getenv("LOG_FILE", str(APP_ROOT / "logs" / "bot.log"))

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus

        return (
            f"postgresql+psycopg://{self.DB_USER}:{quote_plus(self.DB_PASS)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def tz(self):
        from datetime import timezone

        try:
            return ZoneInfo(self.TIMEZONE)
        except Exception:
            # tzdata topilmasa (masalan minimal muhitda) UTC ga qaytamiz.
            return timezone.utc


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
