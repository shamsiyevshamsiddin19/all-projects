import asyncio
import time
import sys
from pathlib import Path
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, func
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))
from app.config import settings
from app.models.stream import Stream, StreamCheck

SEMAPHORE_LIMIT = 30
CHECK_TIMEOUT = 5.0

async def check_single_stream(stream: Stream, sem: asyncio.Semaphore, session_factory):
    async with sem:
        target_url = stream.url_resolved or stream.url
        start_time = time.time()
        status_code = None
        latency_ms = None
        error_msg = None
        headers_seen = {}
        is_ok = False
        sends_cors = False

        try:
            async with httpx.AsyncClient(timeout=CHECK_TIMEOUT, follow_redirects=True) as client:
                # Request only headers / stream start
                req = client.build_request("GET", target_url, headers={"User-Agent": "RadioGlobe-HealthChecker/1.0"})
                res = await client.send(req, stream=True)
                status_code = res.status_code
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Check CORS header
                cors_header = res.headers.get("access-control-allow-origin", "")
                if cors_header in ("*", "https://radio.shamsiyev.uz"):
                    sends_cors = True

                headers_seen = {
                    "content-type": res.headers.get("content-type", ""),
                    "server": res.headers.get("server", ""),
                    "cors": cors_header
                }

                if 200 <= status_code < 400:
                    # Read first byte chunk to verify it is sending data
                    async for _ in res.aiter_bytes(chunk_size=1024):
                        is_ok = True
                        break
                await res.aclose()
        except Exception as e:
            error_msg = str(e)[:250]
            latency_ms = int((time.time() - start_time) * 1000)

        # Update in database
        async with session_factory() as session:
            check_record = StreamCheck(
                stream_id=stream.id,
                status_code=status_code,
                latency_ms=latency_ms,
                error=error_msg,
                headers_seen=headers_seen
            )
            session.add(check_record)

            now = datetime.now(timezone.utc)
            if is_ok:
                score = min(100, stream.score + 5)
                fail_count = 0
                last_ok_at = now
                is_active = True
            else:
                fail_count = stream.fail_count + 1
                score = max(0, stream.score - 20)
                last_ok_at = stream.last_ok_at
                is_active = fail_count < 5

            await session.execute(
                update(Stream)
                .where(Stream.id == stream.id)
                .values(
                    score=score,
                    fail_count=fail_count,
                    last_ok_at=last_ok_at,
                    sends_cors=sends_cors,
                    needs_proxy=not (stream.is_https and sends_cors),
                    is_active=is_active
                )
            )
            await session.commit()

async def run_health_check(limit: int = 50):
    print(f"🩺 Health check boshlandi (tekshirish limiti: {limit})...")
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        streams_res = await session.execute(
            select(Stream).order_by(Stream.last_ok_at.asc().nulls_first()).limit(limit)
        )
        streams = streams_res.scalars().all()

    print(f"{len(streams)} ta oqim navbatga olindi.")
    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
    tasks = [check_single_stream(s, sem, session_factory) for s in streams]
    await asyncio.gather(*tasks)

    print("✅ Health check yakunlandi!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_health_check(30))
