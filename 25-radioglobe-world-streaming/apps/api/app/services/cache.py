"""Redis kesh yordamchisi.

Qoida: kesh ixtiyoriy. Redis yiqilsa yoki javob bermasa — so'rov baribir
bajariladi, faqat sekinroq. Hech qachon kesh sababli xato qaytmasligi kerak.
"""

import json
import logging
from typing import Any, Callable, Awaitable, Optional

logger = logging.getLogger(__name__)


async def cached_json(
    redis,
    key: str,
    ttl: int,
    producer: Callable[[], Awaitable[Any]],
) -> Any:
    """Keshdan o'qiydi, bo'lmasa `producer()` ni chaqirib natijani yozadi."""
    if redis is None:
        return await producer()

    try:
        raw = await redis.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception as exc:
        logger.debug("Kesh o'qilmadi (%s): %s", key, exc)

    value = await producer()

    try:
        await redis.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception as exc:
        logger.debug("Kesh yozilmadi (%s): %s", key, exc)

    return value


async def invalidate(redis, *keys: str) -> None:
    if redis is None or not keys:
        return
    try:
        await redis.delete(*keys)
    except Exception:
        pass
