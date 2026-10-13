from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from typing import List, Optional
from app.database import get_db
from app.models.country import Country
from app.models.channel import Channel, ChannelCountry
from app.models.stream import Stream
from app.schemas.channel import ChannelSimple, ChannelDetail, ChannelListResponse
from app.schemas.stream import StreamInfo
from app.services.token_service import generate_stream_token
from app.config import settings

router = APIRouter(tags=["Channels"])

def format_stream_info(stream: Stream) -> StreamInfo:
    token = generate_stream_token(stream.id)
    play_url = f"{settings.PROXY_BASE_URL}/{stream.id}?t={token}" if stream.needs_proxy else stream.url
    return StreamInfo(
        id=stream.id,
        format=stream.format or "mp3",
        bitrate=stream.bitrate or 128,
        is_https=stream.is_https,
        needs_proxy=stream.needs_proxy,
        score=stream.score,
        play_url=play_url
    )

@router.get("/countries/{slug}/channels", response_model=ChannelListResponse)
async def list_country_channels(
    slug: str,
    type: str = Query("radio", pattern="^(radio|tv)$"),
    sort: str = Query("popular", pattern="^(popular|name|bitrate)$"),
    tag: Optional[str] = None,
    lang: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    country_res = await db.execute(select(Country).where(Country.slug == slug))
    country = country_res.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    query = (
        select(Channel)
        .join(ChannelCountry, ChannelCountry.channel_id == Channel.id)
        .where(
            ChannelCountry.country_iso2 == country.iso2,
            Channel.type == type,
            Channel.is_archived == False
        )
    )

    if tag:
        query = query.where(Channel.tags.contains([tag]))
    if lang:
        query = query.where(Channel.languages.contains([lang]))

    if sort == "name":
        query = query.order_by(asc(Channel.name))
    elif sort == "bitrate":
        query = query.order_by(desc(Channel.bitrate_max), desc(Channel.popularity))
    else:
        query = query.order_by(desc(Channel.popularity), asc(Channel.name))

    if cursor:
        query = query.offset(cursor)
    query = query.limit(limit)

    channels_res = await db.execute(query)
    channels = channels_res.scalars().all()

    items: List[ChannelSimple] = []
    for ch in channels:
        # Load streams for channel
        streams_res = await db.execute(
            select(Stream)
            .where(Stream.channel_id == ch.id, Stream.is_active == True, Stream.score > 20)
            .order_by(desc(Stream.score))
        )
        streams = streams_res.scalars().all()
        primary_stream = format_stream_info(streams[0]) if streams else None

        items.append(
            ChannelSimple(
                id=ch.id,
                type=ch.type,
                slug=ch.slug,
                name=ch.name,
                logo_url=ch.logo_url,
                tags=ch.tags or [],
                languages=ch.languages or [],
                bitrate=ch.bitrate_max or 128,
                score=primary_stream.score if primary_stream else 0,
                primary_stream=primary_stream
            )
        )

    next_cursor = (cursor or 0) + len(items) if len(items) == limit else None
    return ChannelListResponse(
        total=len(items),
        items=items,
        next_cursor=next_cursor
    )


@router.get("/channels/{slug}", response_model=ChannelDetail)
async def get_channel_detail(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    channel_res = await db.execute(select(Channel).where(Channel.slug == slug))
    channel = channel_res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    streams_res = await db.execute(
        select(Stream)
        .where(Stream.channel_id == channel.id, Stream.is_active == True)
        .order_by(desc(Stream.score))
    )
    streams = streams_res.scalars().all()
    stream_infos = [format_stream_info(s) for s in streams]
    primary_stream = stream_infos[0] if stream_infos else None

    return ChannelDetail(
        id=channel.id,
        type=channel.type,
        slug=channel.slug,
        name=channel.name,
        logo_url=channel.logo_url,
        homepage=channel.homepage,
        tags=channel.tags or [],
        languages=channel.languages or [],
        bitrate=channel.bitrate_max or 128,
        score=primary_stream.score if primary_stream else 0,
        primary_stream=primary_stream,
        popularity=channel.popularity,
        streams=stream_infos
    )
