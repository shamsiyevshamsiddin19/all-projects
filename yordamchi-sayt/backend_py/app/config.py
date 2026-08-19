"""Ilova konfiguratsiyasi — barcha maxfiy ma'lumotlar muhit o'zgaruvchilaridan (.env) o'qiladi.

PHP versiyasida baza paroli kodga yozib qo'yilgan va git'ga tushган edi. Bu versiyada
hech qanday maxfiy ma'lumot kodda yo'q — hammasi env orqali beriladi.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv

    # .env faylini backend_py/ ildizidan yuklaymiz (mavjud bo'lsa).
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:  # dotenv o'rnatilmagan bo'lsa ham ishlashda davom etamiz
    pass


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


APP_ROOT = Path(__file__).resolve().parent.parent  # backend_py/
# Statik frontend (index.html, assets/ ...) — PHP loyihaning ildizi:
FRONTEND_ROOT = Path(os.getenv("FRONTEND_ROOT", str(APP_ROOT.parent))).resolve()


class Settings:
    # --- Yo'llar (modul-darajadagi qiymatlar; instansiya orqali ham ochiq) ---
    APP_ROOT: Path = APP_ROOT
    FRONTEND_ROOT: Path = FRONTEND_ROOT

    # --- Baza (PostgreSQL) ---
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = _int("DB_PORT", 5432)
    DB_NAME: str = os.getenv("DB_NAME", "yordamchi")
    DB_USER: str = os.getenv("DB_USER", "yordamchi")
    DB_PASS: str = os.getenv("DB_PASS", "")
    DB_POOL_SIZE: int = _int("DB_POOL_SIZE", 5)
    DB_MAX_OVERFLOW: int = _int("DB_MAX_OVERFLOW", 10)

    # --- Sessiya / xavfsizlik ---
    # Ishlab chiqarishda ALBATTA uzun tasodifiy qiymat bering (yo'q bo'lsa app ishga tushmaydi).
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "")
    SESSION_COOKIE: str = os.getenv("SESSION_COOKIE", "yordamchi_session")
    SESSION_HTTPS_ONLY: bool = _bool("SESSION_HTTPS_ONLY", True)
    SESSION_MAX_AGE: int = _int("SESSION_MAX_AGE", 60 * 60 * 24 * 30)  # 30 kun

    # Yozuv (mutatsiya) endpoint'lari uchun login talab qilinsinmi?
    # Bu ilova login talab qilmaydi (hamma umumiy fazoda ishlaydi), shuning uchun default False.
    REQUIRE_AUTH: bool = _bool("REQUIRE_AUTH", False)

    # Debug rejimi: True bo'lsa xatolik tafsilotlari javobga chiqadi (faqat local uchun).
    DEBUG: bool = _bool("APP_DEBUG", False)

    # CORS: frontend boshqa domendan chaqirsa (odatda bir domen — bo'sh qoldiring).
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ]

    # Statik frontend'ni shu app o'zi tarqatsinmi (True) yoki nginx qilsinmi (False)?
    SERVE_STATIC: bool = _bool("SERVE_STATIC", False)

    # LOKAL uchun: `/boost/*` chaqiruvlarini Boostday bot xizmatiga yo'naltirish manzili.
    # Bo'sh bo'lsa (production'da nginx yo'naltiradi) proxy o'chirilgan.
    BOOST_PROXY_URL: str = os.getenv("BOOST_PROXY_URL", "")
    # Boostday bot API (sayt shu orqali rejalarni boshqaradi)
    BOOST_API_URL: str = os.getenv("BOOST_API_URL", "http://127.0.0.1:8090/boost/api")
    BOOST_SITE_SECRET: str = os.getenv("BOOST_SITE_SECRET", "")

    # --- Fayllar ---
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(FRONTEND_ROOT / "uploads")))
    ICON_DIR: Path = Path(os.getenv("ICON_DIR", str(FRONTEND_ROOT / "assets" / "icons")))
    MANIFEST_FILE: Path = Path(
        os.getenv("MANIFEST_FILE", str(FRONTEND_ROOT / "manifest.webmanifest"))
    )
    REJA_MAX_BYTES: int = _int("REJA_MAX_BYTES", 50 * 1024 * 1024)
    ICON_MAX_BYTES: int = _int("ICON_MAX_BYTES", 2 * 1024 * 1024)
    # Bitta app_storage yozuvining maksimal hajmi (bazani to'ldirishdan himoya).
    STORAGE_MAX_VALUE_BYTES: int = _int("STORAGE_MAX_VALUE_BYTES", 5 * 1024 * 1024)

    # --- Login rate-limit (brute-force himoyasi) ---
    LOGIN_MAX_ATTEMPTS: int = _int("LOGIN_MAX_ATTEMPTS", 8)
    LOGIN_WINDOW_SECONDS: int = _int("LOGIN_WINDOW_SECONDS", 300)
    # Umumiy so'rov cheklovi (bir IP uchun). 0 = o'chirilgan.
    # Oddiy foydalanishda daqiqasiga ~30-60 so'rov bo'ladi, 300 keng zaxira qoldiradi.
    RATE_LIMIT_REQUESTS: int = _int("RATE_LIMIT_REQUESTS", 300)
    RATE_LIMIT_WINDOW_SECONDS: int = _int("RATE_LIMIT_WINDOW_SECONDS", 60)

    # --- Log ---
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", str(APP_ROOT / "logs")))

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus

        return (
            f"postgresql+psycopg://{self.DB_USER}:{quote_plus(self.DB_PASS)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.SESSION_SECRET:
        # Local debug'da avtomatik vaqtinchalik kalit; prod'da xato tashlaymiz.
        if s.DEBUG:
            s.SESSION_SECRET = "dev-insecure-secret-change-me"
        else:
            raise RuntimeError(
                "SESSION_SECRET muhit o'zgaruvchisi berilmagan. "
                "Ishlab chiqarishda uzun tasodifiy qiymat bering: "
                "`openssl rand -hex 32`"
            )
    return s


settings = get_settings()
