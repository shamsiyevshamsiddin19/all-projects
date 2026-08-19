"""Ma'lumotlar bazasi ulanishi (SQLAlchemy async).

PostgreSQL (asyncpg) bilan ishlaydi. 1GB RAM server uchun
pool_size=5 optimal — har bir ulanish ~2-5MB RAM oladi.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Mavjud jadvallarga keyin qo'shilgan ustunlar (Alembic o'rniga engil
# migratsiya). PostgreSQL "ADD COLUMN IF NOT EXISTS" — qayta ishga tushishda
# xavfsiz (ustun bor bo'lsa e'tiborsiz o'tadi).
_MIGRATIONS = (
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by INTEGER "
    "REFERENCES users(id)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_videos INTEGER "
    "DEFAULT 0 NOT NULL",
    "ALTER TABLE payments ADD COLUMN IF NOT EXISTS meta VARCHAR(2000)",
)


async def init_db() -> None:
    """Jadvallarni yaratadi (yo'q bo'lsa) va engil migratsiyalarni qo'llaydi."""
    from sqlalchemy import text

    from db import models  # noqa: F401 — modellarni ro'yxatga olish uchun

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _MIGRATIONS:
            try:
                await conn.execute(text(stmt))
            except Exception:  # noqa: BLE001 — migratsiya botni to'xtatmasin
                pass
