"""Davlatlar ro'yxati va tafsiloti."""

from collections import Counter
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.models.channel import Channel, ChannelCountry
from app.models.country import Country
from app.models.stream import Stream
from app.schemas.country import CountryDetail, CountrySimple
from app.services.cache import cached_json

router = APIRouter(prefix="/countries", tags=["Countries"])

COUNTRY_LIST_TTL = 600
COUNTRY_DETAIL_TTL = 900


@router.get("", response_model=List[CountrySimple])
async def list_countries(
    response: Response,
    limit: int = Query(300, ge=1, le=300),
    has_stations: bool = Query(False, description="Faqat radiosi bor davlatlar"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=3600"

    async def produce():
        query = select(Country)
        if has_stations:
            query = query.where(Country.radio_count > 0)
        query = query.order_by(desc(Country.radio_count), asc(Country.name_en)).limit(limit)
        rows = (await db.execute(query)).scalars().all()
        return [CountrySimple.model_validate(row).model_dump() for row in rows]

    return await cached_json(
        redis, f"countries:list:{limit}:{int(has_stations)}", COUNTRY_LIST_TTL, produce
    )


@router.get("/{slug}", response_model=CountryDetail)
async def get_country_detail(
    slug: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=3600"

    country = (
        await db.execute(select(Country).where(Country.slug == slug))
    ).scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Davlat topilmadi")

    async def produce():
        # Eng mashhur teglar va tillar — har so'rovda qayta hisoblash qimmat,
        # shuning uchun natija keshlanadi
        rows = (
            await db.execute(
                select(Channel.tags, Channel.languages)
                .join(ChannelCountry, ChannelCountry.channel_id == Channel.id)
                .join(Stream, Stream.channel_id == Channel.id)
                .where(
                    ChannelCountry.country_iso2 == country.iso2,
                    Channel.is_archived.is_(False),
                    Stream.is_active.is_(True),
                )
                .limit(500)
            )
        ).all()

        tag_counter: Counter = Counter()
        lang_counter: Counter = Counter()
        for tags, languages in rows:
            tag_counter.update(tags or [])
            lang_counter.update(languages or [])

        centroid = None
        if country.centroid_lat is not None and country.centroid_lon is not None:
            centroid = [country.centroid_lat, country.centroid_lon]

        return CountryDetail(
            iso2=country.iso2,
            iso3=country.iso3,
            m49=country.m49,
            name_uz=country.name_uz,
            name_en=country.name_en,
            slug=country.slug,
            continent=country.continent,
            flag_emoji=country.flag_emoji,
            radio_count=country.radio_count,
            tv_count=country.tv_count,
            centroid=centroid,
            bbox=country.bbox,
            top_tags=[tag for tag, _ in tag_counter.most_common(8)],
            languages=[lang for lang, _ in lang_counter.most_common(5)],
        ).model_dump()

    return await cached_json(redis, f"country:detail:{slug}", COUNTRY_DETAIL_TTL, produce)
