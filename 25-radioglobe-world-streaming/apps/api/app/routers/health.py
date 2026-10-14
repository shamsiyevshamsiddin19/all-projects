import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, get_redis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Xizmat holati.

    Diqqat: bu endpoint ochiq, shuning uchun ichki xato matnlari (ulanish
    satrlari, host nomlari) javobga QO'SHILMAYDI — faqat logga yoziladi.
    """
    db_ok = True
    redis_ok = True

    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_ok = False
        logger.error("Health: ma'lumotlar bazasi javob bermadi: %s", exc)

    try:
        if redis is None:
            redis_ok = False
        else:
            await redis.ping()
    except Exception as exc:
        redis_ok = False
        logger.error("Health: Redis javob bermadi: %s", exc)

    healthy = db_ok and redis_ok
    if not healthy:
        response.status_code = 503

    return {
        "status": "healthy" if healthy else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "version": settings.VERSION,
    }
