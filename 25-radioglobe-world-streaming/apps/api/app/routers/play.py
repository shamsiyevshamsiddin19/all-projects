from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, get_redis
from app.models.stream import Stream
from app.models.channel import Channel
from app.schemas.stream import PlayRequest, PlayResponse
from app.services.token_service import generate_stream_token
from app.config import settings
import httpx

router = APIRouter(tags=["Play"])

async def notify_radio_browser_click(uuid: str):
    """
    Background task to notify radio-browser of a station play click.
    """
    mirror = settings.RADIO_BROWSER_MIRRORS[0]
    click_url = f"https://{mirror}/json/url/{uuid}"
    headers = {"User-Agent": settings.USER_AGENT}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.get(click_url, headers=headers)
    except Exception:
        pass

@router.post("/play", response_model=PlayResponse)
async def report_play(
    req: PlayRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    stream_res = await db.execute(select(Stream).where(Stream.id == req.stream_id))
    stream = stream_res.scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    channel_res = await db.execute(select(Channel).where(Channel.id == stream.channel_id))
    channel = channel_res.scalar_one_or_none()
    station_name = channel.name if channel else "Radio Stream"

    # Increment Redis play counters
    try:
        await redis.incr("radio:plays:total")
        await redis.incr(f"radio:plays:stream:{stream.id}")
        if channel:
            await redis.incr(f"radio:plays:channel:{channel.id}")
    except Exception:
        pass

    # Radio-Browser click feedback
    if channel and isinstance(channel.external_ids, dict):
        uuid = channel.external_ids.get("radiobrowser_uuid")
        if uuid:
            background_tasks.add_task(notify_radio_browser_click, uuid)

    token = generate_stream_token(stream.id)
    play_url = f"{settings.PROXY_BASE_URL}/{stream.id}?t={token}" if stream.needs_proxy else stream.url

    return PlayResponse(
        stream_id=stream.id,
        station_name=station_name,
        play_url=play_url,
        is_proxied=stream.needs_proxy,
        format=stream.format or "mp3"
    )
