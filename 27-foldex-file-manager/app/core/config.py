# -*- coding: utf-8 -*-
"""
Foldex konfiguratsiya moduli.
Ushbu modul pydantic-settings orqali .env fayldan va tizim muhitidan
barcha muhim o'zgaruvchilarni o'qiydi va qat'iy tip tekshiruvini ta'minlaydi.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Loyihaning asosiy ildiz katalogi (27-foldex-file-manager/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Ilovaning barcha sozlamalari va xavfsizlik parametrlarini boshqaruvchi klass.
    Har bir xususiyat o'zbek tilida izohlangan.
    """

    # 1. Loyiha asosiy parametrlari
    PROJECT_NAME: str = Field(default="Foldex File Manager", description="Loyiha nomi")
    ENVIRONMENT: str = Field(default="production", description="Ishlash muhiti (production / development)")
    DEBUG: bool = Field(default=False, description="Nosozliklarni aniqlash rejimi")
    DOMAIN: str = Field(default="https://foldex.shamsiyev.uz", description="Ilovaning asosiy domen manzili")
    HOST: str = Field(default="0.0.0.0", description="FastAPI server tinglaydigan tarmoq manzili")
    PORT: int = Field(default=8000, description="FastAPI server porti")

    # 2. Telegram Bot sozlamalari va qat'iy xavfsizlik cheklovi
    BOT_TOKEN: str = Field(default="", description="Telegram BotFather bergan bot API tokeni")
    # Yagona ruxsat berilgan admin Telegram ID raqami (talab bo'yicha: 7883409434)
    TELEGRAM_ADMIN_ID: int = Field(
        default=7883409434,
        description="Faqat ushbu ID ga ega administrator barcha funksiyalardan foydalana oladi"
    )
    WEBHOOK_SECRET: str = Field(
        default="foldex_super_secret_webhook_key_2026",
        description="Telegram Webhook xavfsizlik tokeni (X-Telegram-Bot-Api-Secret-Token)"
    )
    USE_WEBHOOK: bool = Field(
        default=True,
        description="True bo'lsa webhook rejimi ishlatiladi, False bo'lsa polling"
    )

    # 3. JWT va Web Sessiyalar xavfsizligi
    JWT_SECRET_KEY: str = Field(
        default="foldex_jwt_secret_shamsiyev_uz_secure_key_123456789",
        description="JWT tokenlarni imzolash uchun kriptografik maxfiy kalit"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT imzolash algoritmi")
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        description="Admin sessiyasining amal qilish muddati (kunlarda)"
    )

    # 4. PostgreSQL Ma'lumotlar bazasi
    POSTGRES_USER: str = Field(default="foldex_user", description="PostgreSQL foydalanuvchi nomi")
    POSTGRES_PASSWORD: str = Field(default="secure_foldex_db_password", description="PostgreSQL paroli")
    POSTGRES_DB: str = Field(default="foldex_db", description="PostgreSQL ma'lumotlar bazasi nomi")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL xost manzili")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL porti")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://foldex_user:secure_foldex_db_password@localhost:5432/foldex_db",
        description="Asinxron SQLAlchemy uchun to'liq ulanish URL manzili"
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql://foldex_user:secure_foldex_db_password@localhost:5432/foldex_db",
        description="Sinxron Alembic migratsiyalari uchun ulanish URL manzili"
    )

    # 5. Fayllarni saqlash sozlamalari
    STORAGE_DIR: str = Field(
        default=str(BASE_DIR / "uploads"),
        description="Fayllar diskda saqlanadigan asosiy papka manzili"
    )
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=500,
        description="Yuklanishi mumkin bo'lgan maksimal fayl hajmi (Megabaytlarda)"
    )

    # Pydantic v2 sozlamalari: .env faylidan o'qish
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Maksimal fayl hajmini baytlarda hisoblab qaytaradi."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Yagona global sozlamalar obyektini yaratish
settings = Settings()

# Yuklamalar papkasi mavjud bo'lmasa, avtomatik yaratish
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
