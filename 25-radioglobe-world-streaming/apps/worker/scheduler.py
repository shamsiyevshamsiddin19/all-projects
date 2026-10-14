"""Worker konteynerining asosiy jarayoni.

Oldin Dockerfile to'g'ridan-to'g'ri `health_checker.py` ni ishga tushirardi:
skript 30 ta oqimni tekshirib tugardi, `restart: unless-stopped` esa uni
darhol qayta ishga tushirardi — ya'ni cheksiz qayta ishga tushish sikli,
hech qanday jadvalsiz. Endi bitta uzoq ishlaydigan jarayon vazifalarni
o'z vaqtida bajaradi.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))

from app.config import settings  # noqa: E402
from app.models.channel import Channel  # noqa: E402
from app.models.country import Country  # noqa: E402

from health_checker import cleanup_old_checks, run_health_check  # noqa: E402
from ingest import ingest_stations  # noqa: E402
from seed_countries import seed_countries  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [worker] %(message)s")
logger = logging.getLogger("scheduler")

HEALTH_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL_MINUTES", "10")) * 60
INGEST_INTERVAL = int(os.getenv("INGEST_INTERVAL_HOURS", "24")) * 3600
CLEANUP_INTERVAL = 24 * 3600
STARTUP_DELAY = int(os.getenv("WORKER_STARTUP_DELAY", "15"))


async def _table_counts() -> tuple[int, int]:
    engine = create_async_engine(settings.DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            countries = (await session.execute(select(func.count(Country.iso2)))).scalar() or 0
            channels = (await session.execute(select(func.count(Channel.id)))).scalar() or 0
        return countries, channels
    finally:
        await engine.dispose()


async def _safe(name: str, coro_factory) -> None:
    """Vazifani bajaradi; xato bo'lsa logga yozadi, lekin worker'ni to'xtatmaydi."""
    try:
        started = datetime.now(timezone.utc)
        await coro_factory()
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        logger.info("✅ %s yakunlandi (%.0f s)", name, elapsed)
    except Exception:
        logger.exception("❌ %s bajarilmadi", name)


async def bootstrap() -> None:
    """Birinchi ishga tushishda bazani to'ldiradi."""
    countries, channels = await _table_counts()
    logger.info("Baza holati: %d davlat, %d kanal", countries, channels)

    if countries == 0:
        logger.info("Davlatlar jadvali bo'sh — seed boshlanmoqda")
        await _safe("seed_countries", seed_countries)

    if channels == 0:
        logger.info("Kanallar jadvali bo'sh — dastlabki ingest boshlanmoqda")
        await _safe("ingest (dastlabki)", ingest_stations)


async def periodic(name: str, interval: int, coro_factory, initial_delay: int = 0) -> None:
    if initial_delay:
        await asyncio.sleep(initial_delay)
    while True:
        await _safe(name, coro_factory)
        await asyncio.sleep(interval)


async def main() -> None:
    logger.info(
        "Worker ishga tushdi — health: har %d daq, ingest: har %d soat",
        HEALTH_INTERVAL // 60, INGEST_INTERVAL // 3600,
    )
    # API migratsiyalarni bajarib bo'lishini kutamiz
    await asyncio.sleep(STARTUP_DELAY)

    await bootstrap()

    await asyncio.gather(
        periodic("health_check", HEALTH_INTERVAL, run_health_check),
        periodic("ingest", INGEST_INTERVAL, ingest_stations, initial_delay=INGEST_INTERVAL),
        periodic("cleanup", CLEANUP_INTERVAL, cleanup_old_checks, initial_delay=3600),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker to'xtatildi")
