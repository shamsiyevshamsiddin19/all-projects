"""Oqimlarning tirikligini tekshiradi — katalog sifatining asosi.

Oldingi versiyadagi asosiy xato: navbat `last_ok_at` (oxirgi MUVAFFAQIYAT)
bo'yicha tuzilardi. Hech qachon ishlamagan oqimda u abadiy NULL bo'lib qolardi,
shuning uchun har yurishda yana o'sha o'lik oqimlar birinchi tekshirilib,
katalogning qolgan qismi navbatga umuman yetmasdi.

Endi navbat `next_check_at` bo'yicha va har tekshiruvdan keyin u exponential
backoff bilan oldinga suriladi.
"""

import asyncio
import logging
import os
import sys
from typing import Optional
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import delete, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))

from app.config import settings  # noqa: E402
from app.models.stream import Stream, StreamCheck  # noqa: E402

logger = logging.getLogger("health_checker")

CONCURRENCY = int(os.getenv("HEALTH_CHECK_CONCURRENCY", "30"))
CHECK_TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT", "8"))
CHECK_HISTORY_DAYS = int(os.getenv("CHECK_HISTORY_DAYS", "90"))

# Backoff bosqichlari: ketma-ket nechta xatodan keyin qancha kutiladi
BACKOFF_MINUTES = {
    0: 60,      # ishlayapti → 1 soat
    1: 120,     # 1 xato → 2 soat
    2: 360,     # 2 xato → 6 soat
    3: 720,     # 3 xato → 12 soat
}
BACKOFF_MAX_MINUTES = 1440  # 4+ xato → kuniga 1 marta
DEACTIVATE_AFTER_FAILURES = 5


def _next_check_delay(fail_count: int) -> timedelta:
    minutes = BACKOFF_MINUTES.get(fail_count, BACKOFF_MAX_MINUTES)
    return timedelta(minutes=minutes)


async def check_one(stream_id: int, url: str, sem: asyncio.Semaphore) -> dict:
    """Bitta oqimni tekshiradi. Bazaga tegmaydi — faqat natija qaytaradi."""
    async with sem:
        started = time.monotonic()
        result = {
            "stream_id": stream_id,
            "ok": False,
            "status_code": None,
            "latency_ms": None,
            "error": None,
            "sends_cors": False,
            "is_geo_blocked": False,
            "headers_seen": {},
        }

        try:
            async with httpx.AsyncClient(
                timeout=CHECK_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": settings.USER_AGENT},
            ) as client:
                request = client.build_request("GET", url)
                response = await client.send(request, stream=True)
                result["status_code"] = response.status_code
                result["latency_ms"] = int((time.monotonic() - started) * 1000)

                cors = response.headers.get("access-control-allow-origin", "")
                result["sends_cors"] = cors == "*" or cors in settings.ALLOWED_ORIGINS
                result["headers_seen"] = {
                    "content-type": response.headers.get("content-type", "")[:100],
                    "server": response.headers.get("server", "")[:100],
                    "cors": cors[:100],
                    "icy-name": response.headers.get("icy-name", "")[:100],
                }

                # 403 odatda hududiy cheklov degani
                if response.status_code == 403:
                    result["is_geo_blocked"] = True

                if 200 <= response.status_code < 300:
                    # Status yetarli emas — ba'zi serverlar 200 qaytarib,
                    # keyin bitta ham bayt yubormaydi. Haqiqiy ma'lumot kelishini
                    # tekshiramiz.
                    async for chunk in response.aiter_bytes(chunk_size=2048):
                        if chunk:
                            result["ok"] = True
                        break

                await response.aclose()

        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"[:300]
            result["latency_ms"] = int((time.monotonic() - started) * 1000)

        return result


async def run_health_check(batch_size: Optional[int] = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    limit = batch_size or int(os.getenv("HEALTH_CHECK_BATCH", "300"))

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    async with session_factory() as session:
        # Navbat: vaqti kelganlar, eng uzoq kutganidan boshlab
        rows = (
            await session.execute(
                select(Stream.id, Stream.url, Stream.url_resolved, Stream.is_https)
                .where(or_(Stream.next_check_at.is_(None), Stream.next_check_at <= now))
                .order_by(Stream.next_check_at.asc().nulls_first())
                .limit(limit)
            )
        ).all()

    if not rows:
        logger.info("Tekshirish vaqti kelgan oqim yo'q")
        await engine.dispose()
        return

    logger.info("🩺 %d ta oqim navbatga olindi (parallellik: %d)", len(rows), CONCURRENCY)

    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*[
        check_one(row.id, row.url_resolved or row.url, sem) for row in rows
    ])

    https_by_id = {row.id: row.is_https for row in rows}
    ok_count = 0

    # Barcha yangilanishlar bitta sessiyada — oldin har oqim uchun alohida
    # sessiya ochilardi (30 ta parallel ulanish)
    async with session_factory() as session:
        for res in results:
            stream = await session.get(Stream, res["stream_id"])
            if stream is None:
                continue

            session.add(StreamCheck(
                stream_id=res["stream_id"],
                ok=res["ok"],
                status_code=res["status_code"],
                latency_ms=res["latency_ms"],
                error=res["error"],
                headers_seen=res["headers_seen"],
            ))

            if res["ok"]:
                ok_count += 1
                stream.score = min(100, stream.score + 10)
                stream.fail_count = 0
                stream.last_ok_at = now
                stream.is_active = True
                stream.latency_ms = res["latency_ms"]
            else:
                stream.fail_count = min(32000, stream.fail_count + 1)
                stream.score = max(0, stream.score - 20)
                stream.is_active = stream.fail_count < DEACTIVATE_AFTER_FAILURES

            stream.sends_cors = res["sends_cors"]
            stream.is_geo_blocked = res["is_geo_blocked"]
            # To'g'ridan-to'g'ri ijro faqat HTTPS + CORS bo'lsa mumkin;
            # qolgan hamma holatda proxy kerak
            stream.needs_proxy = not (https_by_id.get(res["stream_id"], False) and res["sends_cors"])
            stream.last_check_at = now
            stream.next_check_at = now + _next_check_delay(stream.fail_count)

        await session.commit()

    await engine.dispose()
    logger.info(
        "✅ Tekshirildi: %d, ishlayapti: %d (%.0f%%), nosoz: %d",
        len(results), ok_count, 100 * ok_count / len(results), len(results) - ok_count,
    )


async def cleanup_old_checks() -> None:
    """Partitsiyalarni boshqaradi: yangisini yaratadi, eskisini o'chiradi.

    Migratsiya 6 oylik partitsiya yaratadi. Bu vazifa bo'lmasa, yarim yildan
    keyin barcha yozuvlar `default` partitsiyaga to'planib qolardi va
    partitsiyalashdan kutilgan foyda yo'qolardi.
    """
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Kelgusi 3 oy uchun partitsiyalar
        await session.execute(text("""
            DO $$
            DECLARE
                p_start DATE; p_end DATE; p_name TEXT; i INT;
            BEGIN
                FOR i IN 0..3 LOOP
                    p_start := (date_trunc('month', now()) + (i || ' month')::interval)::date;
                    p_end   := p_start + INTERVAL '1 month';
                    p_name  := 'stream_checks_' || to_char(p_start, 'YYYY_MM');
                    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = p_name) THEN
                        EXECUTE format(
                            'CREATE TABLE %I PARTITION OF stream_checks
                             FOR VALUES FROM (%L) TO (%L)', p_name, p_start, p_end);
                    END IF;
                END LOOP;
            END $$;
        """))

        # Saqlash muddatidan oshgan partitsiyalarni butunlay tashlab yuborish —
        # DELETE dan ancha arzon.
        # DO bloki bind parametr qabul qilmaydi, shuning uchun qiymat to'g'ridan-
        # to'g'ri qo'yiladi (u env dan olingan butun son, SQL-injection xavfi yo'q).
        retention_months = max(1, CHECK_HISTORY_DAYS // 30)
        await session.execute(text(f"""
            DO $$
            DECLARE
                cutoff DATE := (date_trunc('month', now())
                                - INTERVAL '{retention_months} month')::date;
                r RECORD;
            BEGIN
                FOR r IN
                    SELECT c.relname FROM pg_class c
                    JOIN pg_inherits i ON c.oid = i.inhrelid
                    JOIN pg_class p ON p.oid = i.inhparent
                    WHERE p.relname = 'stream_checks'
                      AND c.relname ~ '^stream_checks_[0-9]{{4}}_[0-9]{{2}}$'
                      AND to_date(right(c.relname, 7), 'YYYY_MM') < cutoff
                LOOP
                    EXECUTE format('DROP TABLE IF EXISTS %I', r.relname);
                END LOOP;
            END $$;
        """))

        # Default partitsiyadagi eskirgan qatorlarni tozalash
        result = await session.execute(
            delete(StreamCheck).where(
                StreamCheck.checked_at
                < datetime.now(timezone.utc) - timedelta(days=CHECK_HISTORY_DAYS)
            )
        )
        await session.commit()
        logger.info(
            "🧹 Partitsiyalar yangilandi, %d ta eskirgan yozuv o'chirildi",
            result.rowcount or 0,
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_health_check())
