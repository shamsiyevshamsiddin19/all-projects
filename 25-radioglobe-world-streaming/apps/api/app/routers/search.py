from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from typing import List, Dict, Any
from app.database import get_db
from app.models.country import Country
from app.models.channel import Channel
from app.models.stream import Stream
from app.schemas.channel import ChannelSimple
from app.schemas.country import CountrySimple
from app.routers.channels import format_stream_info

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("")
async def search_stations_and_countries(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    query_pattern = f"%{q.lower()}%"

    # Search countries
    c_stmt = (
        select(Country)
        .where(
            or_(
                Country.name_en.ilike(query_pattern),
                Country.name_uz.ilike(query_pattern),
                Country.iso2.ilike(query_pattern)
            )
        )
        .order_by(desc(Country.radio_count))
        .limit(5)
    )
    c_res = await db.execute(c_stmt)
    countries = c_res.scalars().all()

    # Search channels
    ch_stmt = (
        select(Channel)
        .where(
            Channel.is_archived == False,
            or_(
                Channel.name.ilike(query_pattern),
                Channel.slug.ilike(query_pattern)
            )
        )
        .order_by(desc(Channel.popularity))
        .limit(limit)
    )
    ch_res = await db.execute(ch_stmt)
    channels = ch_res.scalars().all()

    channel_items: List[ChannelSimple] = []
    for ch in channels:
        streams_res = await db.execute(
            select(Stream)
            .where(Stream.channel_id == ch.id, Stream.is_active == True, Stream.score > 20)
            .order_by(desc(Stream.score))
        )
        streams = streams_res.scalars().all()
        primary_stream = format_stream_info(streams[0]) if streams else None

        channel_items.append(
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

    return {
        "query": q,
        "countries": [
            CountrySimple(
                iso2=c.iso2,
                iso3=c.iso3,
                m49=c.m49,
                name_uz=c.name_uz,
                name_en=c.name_en,
                slug=c.slug,
                continent=c.continent,
                flag_emoji=c.flag_emoji,
                radio_count=c.radio_count,
                tv_count=c.tv_count
            )
            for c in countries
        ],
        "stations": channel_items
    }
