from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db, get_redis

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    db_status = "ok"
    redis_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    try:
        await redis.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0"
    }
