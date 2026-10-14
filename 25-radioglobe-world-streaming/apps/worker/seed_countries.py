"""Davlatlar jadvalini `data/countries.json` dan to'ldiradi (idempotent).

Ma'lumot qo'lda emas, `build_countries.py` tomonidan generatsiya qilinadi.
Skriptni istalgancha qayta ishga tushirish mumkin — mavjud yozuvlar
yangilanadi, hisoblagichlar (radio_count/tv_count) tegilmaydi.
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))

from app.config import settings  # noqa: E402
from app.models.country import Country  # noqa: E402

DATA_FILE = Path(__file__).resolve().parent / "data" / "countries.json"

# Hisoblagichlar bu skript tomonidan O'ZGARTIRILMAYDI — ularni ingest boshqaradi
MUTABLE_FIELDS = (
    "iso3", "m49", "name_en", "name_uz", "slug",
    "continent", "flag_emoji", "centroid_lat", "centroid_lon", "bbox",
)


async def seed_countries() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            f"{DATA_FILE} topilmadi. Avval ishga tushiring: python build_countries.py"
        )

    rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"📦 {len(rows)} ta davlat yozuvi o'qildi")

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created = updated = 0
    async with session_factory() as session:
        existing = {
            c.iso2: c
            for c in (await session.execute(select(Country))).scalars().all()
        }

        for row in rows:
            country = existing.get(row["iso2"])
            if country is None:
                session.add(Country(**row))
                created += 1
                continue

            changed = False
            for field in MUTABLE_FIELDS:
                if getattr(country, field) != row[field]:
                    setattr(country, field, row[field])
                    changed = True
            if changed:
                updated += 1

        await session.commit()

    await engine.dispose()
    print(f"✅ Yaratildi: {created}, yangilandi: {updated}, jami: {len(rows)}")


if __name__ == "__main__":
    asyncio.run(seed_countries())
