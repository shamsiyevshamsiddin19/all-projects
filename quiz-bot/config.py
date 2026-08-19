"""Quiz bot sozlamalari."""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class Settings:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "tez_quizbot")

    _admins = os.getenv("ADMIN_IDS", "").replace(" ", "")
    ADMIN_IDS = [int(x) for x in _admins.split(",") if x] if _admins else []

    # PostgreSQL (asyncpg): postgresql://user:pass@host:5432/dbname
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://quiz:quiz@127.0.0.1:5432/quizbot"
    )

    # Web admin panel
    WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT = int(os.getenv("WEB_PORT", "8095"))
    ADMIN_USER = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "2501")
    # Master (subtitr) panel manzili — dropdown "Subtitr bot" havolasi uchun
    SUBTITR_ADMIN_URL = os.getenv(
        "SUBTITR_ADMIN_URL",
        "https://comes-reforms-preferences-anytime.trycloudflare.com/admin",
    )
    # Master panel /quiz proxy orqali kelganda parolsiz o'tkazish uchun sir
    QUIZ_BRIDGE_SECRET = os.getenv("QUIZ_BRIDGE_SECRET", "")

    # O'yin sozlamalari (default)
    DEFAULT_SHUFFLE = os.getenv("SHUFFLE", "1") == "1"       # savol/variant aralashtirish
    DEFAULT_QUESTION_TIME = int(os.getenv("QUESTION_TIME", "0"))  # sekund, 0=cheksiz

    # Telegram poll cheklovlari
    QUESTION_LIMIT = 300
    OPTION_LIMIT = 100
    MAX_OPTIONS = 10


settings = Settings()
