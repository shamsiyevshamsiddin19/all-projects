import asyncio
import logging
from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


_redis_client: Optional[aioredis.Redis] = None
_redis_lock = asyncio.Lock()


async def get_redis():
    """Redis ulanishini qaytaradi.

    Lock kerak: lock'siz bir vaqtda kelgan ikki so'rov ikkita alohida pool
    yaratib yuboradi va biri "yetim" bo'lib qoladi.

    Redis ishlamasa None qaytadi — kesh va hisoblagichlar ixtiyoriy, ularning
    yo'qligi butun API ni to'xtatmasligi kerak.
    """
    global _redis_client
    if _redis_client is None:
        async with _redis_lock:
            if _redis_client is None:
                try:
                    client = aioredis.from_url(
                        settings.REDIS_URL,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=3,
                        socket_timeout=3,
                        health_check_interval=30,
                    )
                    await client.ping()
                    _redis_client = client
                except Exception as exc:
                    logger.warning("Redis ulanmadi, keshsiz davom etamiz: %s", exc)
                    return None
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
