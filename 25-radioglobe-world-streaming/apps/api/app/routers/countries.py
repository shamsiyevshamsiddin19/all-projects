from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.country import Country
from app.models.channel import Channel, ChannelCountry
from app.schemas.country import CountrySimple, CountryDetail

router = APIRouter(prefix="/countries", tags=["Countries"])

@router.get("", response_model=List[CountrySimple])
async def list_countries(
    limit: int = Query(250, ge=1, le=300),
    has_stations: bool = Query(False, description="Filter only countries with radio_count > 0"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Country)
    if has_stations:
        query = query.where(Country.radio_count > 0)
    query = query.order_by(desc(Country.radio_count), Country.name_en).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{slug}", response_model=CountryDetail)
async def get_country_detail(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Country).where(Country.slug == slug))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Fetch top tags and languages for this country's channels
    channels_query = (
        select(Channel.tags, Channel.languages)
        .join(ChannelCountry, ChannelCountry.channel_id == Channel.id)
        .where(ChannelCountry.country_iso2 == country.iso2, Channel.is_archived == False)
        .limit(100)
    )
    channels_res = await db.execute(channels_query)
    all_tags = []
    all_langs = []
    for tags, langs in channels_res.all():
        if tags:
            all_tags.extend(tags)
        if langs:
            all_langs.extend(langs)

    # Top unique tags
    from collections import Counter
    top_tags = [tag for tag, _ in Counter(all_tags).most_common(8)]
    top_langs = [lang for lang, _ in Counter(all_langs).most_common(5)]

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
        top_tags=top_tags,
        languages=top_langs
    )
