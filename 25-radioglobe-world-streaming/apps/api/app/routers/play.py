import logging

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db, get_redis
from app.models.channel import Channel
from app.models.stream import Stream
from app.schemas.stream import PlayRequest, PlayResponse
from app.services.rate_limit import check_rate_limit, client_ip
from app.services.token_service import build_play_url

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Play"])


async def notify_radio_browser_click(uuid: str) -> None:
    """Radio-browser'ga klik haqida xabar beradi.

    Bu ularning reyting tizimiga hissa — ochiq bazadan foydalanganimiz uchun
    qaytaradigan minimal hurmat.
    """
    headers = {"User-Agent": settings.USER_AGENT}
    for mirror in settings.RADIO_BROWSER_MIRRORS:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"https://{mirror}/json/url/{uuid}", headers=headers)
                if res.status_code == 200:
                    return
        except Exception:
            continue


@router.post("/play", response_model=PlayResponse)
async def report_play(
    req: PlayRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    ip = client_ip(request)
    allowed = await check_rate_limit(
        redis, f"play:{ip}", settings.RATE_LIMIT_PLAY_PER_MIN, window_seconds=60
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="So'rovlar juda tez-tez yuborilmoqda")

    stream = (
        await db.execute(
            select(Stream)
            .options(selectinload(Stream.channel))
            .where(Stream.id == req.stream_id)
        )
    ).scalar_one_or_none()

    if not stream or not stream.is_active:
        raise HTTPException(status_code=404, detail="Oqim topilmadi yoki faol emas")

    channel: Channel | None = stream.channel
    station_name = channel.name if channel else "Radio Stream"

    if redis is not None:
        try:
            pipe = redis.pipeline()
            pipe.incr("radio:plays:total")
            pipe.incr(f"radio:plays:stream:{stream.id}")
            if channel:
                pipe.incr(f"radio:plays:channel:{channel.id}")
            await pipe.execute()
        except Exception as exc:
            logger.debug("Play hisoblagich yangilanmadi: %s", exc)

    if channel and isinstance(channel.external_ids, dict):
        uuid = channel.external_ids.get("radiobrowser_uuid")
        if uuid:
            background_tasks.add_task(notify_radio_browser_click, uuid)

    return PlayResponse(
        stream_id=stream.id,
        station_name=station_name,
        play_url=build_play_url(stream),
        is_proxied=stream.needs_proxy,
        format=stream.format or "mp3",
    )
