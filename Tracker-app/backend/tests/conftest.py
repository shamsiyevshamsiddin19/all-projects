"""Test-wide setup.

Bu bo'lmasa, testlar ilovaning haqiqiy `tracker.db` fayliga yozadi va
birinchi ishga tushirishda o'tadi, lekin qayta ishga tushirilganda
("email allaqachon ro'yxatdan o'tgan" kabi) muvaffaqiyatsiz tugaydi —
chunki oldingi test yozgan qatorlar bazada qolib ketadi.

Bu fayl: (1) sinovlarni alohida, ishchi bazadan butunlay ajratilgan
SQLite faylga yo'naltiradi, (2) har bir test oldidan jadvallarni
tozalab qayta yaratadi — shunda testlar tartibidan qat'i nazar va
necha marta ishga tushirilishidan qat'i nazar bir xil natija beradi.
"""

import os

# DIQQAT: bu import qatoridan oldin bajarilishi shart — app.core.config
# `Settings()` ni import vaqtida yaratadi va DATABASE_URL'ni o'sha yerda
# o'qiydi.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_tracker.db"

import pytest_asyncio  # noqa: E402

from app.core.database import Base, engine  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _clean_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
