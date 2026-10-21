# -*- coding: utf-8 -*-
"""
SQLAlchemy 2.0 asinxron ma'lumotlar bazasi ulanishi moduli.
Ushbu modul asyncpg drayveri yordamida PostgreSQL bilan yuqori tezlikda
asinxron aloqani ta'minlaydi va FastAPI dependency injection uchun get_db ni taqdim etadi.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 1. SQLAlchemy 2.0 uchun asinxron ulanish drayveri (Engine) yaratish
# pool_pre_ping=True: ulanish uzilib qolgan bo'lsa avtomatik yangilaydi
# pool_size=10, max_overflow=20: yuqori yuklamalarda parallel ulanishlarni boshqarish
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True
)

# 2. Asinxron sessiyalar fabrikasi (AsyncSessionmaker)
# expire_on_commit=False: commit qilingandan keyin obyekt atributlariga qayta murojaatda xatolik bermaydi
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# 3. Barcha ma'lumotlar bazasi modellari uchun asosiy DeclarativeBase klassi
class Base(DeclarativeBase):
    """Barcha SQLAlchemy modellarining ota klassi."""
    pass


# 4. FastAPI yo'llari (routes) uchun ma'lumotlar bazasi sessiyasini taqdim etuvchi dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Har bir HTTP so'rovi uchun alohida asinxron DB sessiyasi ochadi,
    so'rov tugagach xatolik bo'lsa rollback qiladi, muvaffaqiyatli bo'lsa yopadi.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
