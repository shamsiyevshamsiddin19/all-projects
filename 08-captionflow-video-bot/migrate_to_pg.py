"""SQLite'dagi mavjud ma'lumotlarni PostgreSQL'ga ko'chirish.

Ishlatish (serverda):
    # 1. Botni to'xtating
    sudo systemctl stop subtitr-bot
    # 2. Migratsiya
    /opt/subtitr_bot/.venv/bin/python migrate_to_pg.py
    # 3. Botni qayta ishga tushiring
    sudo systemctl start subtitr-bot
"""
import sqlite3
import asyncio
import os
import sys
import datetime as dt

# .env ni yuklash uchun
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text


SQLITE_PATH = os.getenv("SQLITE_PATH", "subtitr.db")
PG_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://subtitr:SubT1r_Pg2026!@localhost:5432/subtitr_db")


# Jadvallar va ustunlari (SQLite'dan o'qish tartibi)
TABLES = [
    ("users", [
        "id", "telegram_id", "username", "language", "plan", "plan_until",
        "is_blocked", "created_at", "last_active_at",
    ]),
    ("videos", [
        "id", "user_id", "source_type", "mode", "target_lang", "status",
        "error_step", "error_message", "duration_seconds",
        "translation_provider", "created_at", "finished_at",
    ]),
    ("payments", [
        "id", "user_id", "plan", "amount", "status", "provider",
        "click_trans_id", "created_at", "paid_at",
    ]),
    ("donations", [
        "id", "user_id", "amount", "comment", "status", "click_trans_id",
        "is_approved", "is_public", "created_at", "paid_at",
    ]),
    ("settings", [
        "key", "value", "updated_at",
    ]),
]


async def migrate():
    if not os.path.isfile(SQLITE_PATH):
        print(f"SQLite fayl topilmadi: {SQLITE_PATH}")
        sys.exit(1)

    print(f"SQLite: {SQLITE_PATH}")
    print(f"PostgreSQL: {PG_URL.split('@')[1] if '@' in PG_URL else PG_URL}")

    # SQLite'dan o'qish
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row

    # PostgreSQL ga yozish
    engine = create_async_engine(PG_URL, echo=False)

    # Avval jadvallarni yaratish (modellardan)
    from db.base import Base
    from db import models  # noqa: F401
    async with engine.begin() as pg_conn:
        await pg_conn.run_sync(Base.metadata.drop_all)
        await pg_conn.run_sync(Base.metadata.create_all)
    print("PostgreSQL jadvallar yaratildi")

    async_sess = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    total = 0
    for table_name, columns in TABLES:
        try:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            print(f"  {table_name}: jadval yo'q (o'tkazib yuborildi)")
            continue

        if not rows:
            print(f"  {table_name}: bo'sh")
            continue

        # SQLite row'dan faqat mavjud ustunlarni olish
        sqlite_cols = [desc[0] for desc in cursor.description]
        common_cols = [c for c in columns if c in sqlite_cols]

        async with async_sess() as session:
            for row in rows:
                values = {}
                for col in common_cols:
                    val = row[col]
                    # Boolean -> int -> bool (SQLite 0/1)
                    if col in ("is_blocked", "is_approved", "is_public") and val is not None:
                        val = bool(val)
                    # Date string -> datetime object (PostgreSQL qat'iy)
                    if col in ("created_at", "last_active_at", "plan_until", "paid_at", "updated_at", "finished_at") and val is not None:
                        if isinstance(val, str):
                            # Try parsing SQLite ISO format "YYYY-MM-DD HH:MM:SS.mmmmmm"
                            try:
                                val = dt.datetime.fromisoformat(val)
                            except ValueError:
                                # Yoki bo'sh joy bilan formatlangan
                                pass
                    values[col] = val

                cols_str = ", ".join(values.keys())
                params_str = ", ".join(f":{k}" for k in values.keys())
                await session.execute(
                    text(f"INSERT INTO {table_name} ({cols_str}) VALUES ({params_str}) ON CONFLICT DO NOTHING"),
                    values,
                )
            await session.commit()

        # Sequence'ni to'g'rilash (id ustuni bo'lsa)
        if "id" in common_cols:
            async with async_sess() as session:
                max_id = conn.execute(f"SELECT MAX(id) FROM {table_name}").fetchone()[0]
                if max_id:
                    seq_name = f"{table_name}_id_seq"
                    await session.execute(
                        text(f"SELECT setval('{seq_name}', :val, true)"),
                        {"val": max_id},
                    )
                    await session.commit()

        count = len(rows)
        total += count
        print(f"  {table_name}: {count} ta yozuv ko'chirildi")

    conn.close()
    await engine.dispose()
    print(f"\nJami: {total} ta yozuv ko'chirildi ✅")


if __name__ == "__main__":
    asyncio.run(migrate())
