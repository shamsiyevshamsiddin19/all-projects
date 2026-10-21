"""Katalog statistikasi va tasodifiy stansiya.

Bu endpointlar interfeysdagi raqamlarni HAQIQIY qiladi. Ilgari bosh sahifada
"FREQ: 104.2 MHZ", "ORBIT: GEO-STATIONARY" kabi o'ylab topilgan qiymatlar
turardi — ular hech narsani anglatmasdi va mahsulotni maketga o'xshatib
qo'yardi.
"""

import logging
import random
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, get_redis
from app.models.channel import Channel, ChannelCountry
from app.models.country import Country
from app.models.stream import Stream
from app.routers.channels import MIN_PLAYABLE_SCORE, to_simple
from app.services.cache import cached_json

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Stats"])

STATS_TTL = 600


def _playable_exists():
    return (
        select(Stream.channel_id)
        .where(
            Stream.channel_id == Channel.id,
            Stream.is_active.is_(True),
            Stream.score > MIN_PLAYABLE_SCORE,
            Stream.is_geo_blocked.is_(False),
        )
        .exists()
    )


@router.get("/stats")
async def get_stats(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Bosh sahifadagi raqamlar uchun yagona manba."""
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"

    async def produce():
        playable = _playable_exists()

        stations = (
            await db.execute(
                select(func.count(Channel.id)).where(
                    Channel.is_archived.is_(False),
                    Channel.type == "radio",
                    playable,
                )
            )
        ).scalar() or 0

        countries = (
            await db.execute(
                select(func.count(Country.iso2)).where(Country.radio_count > 0)
            )
        ).scalar() or 0

        # Eng ko'p uchraydigan janrlar — namuna bo'yicha hisoblanadi, chunki
        # barcha kanallarni skanerlash har so'rovda qimmat tushadi
        tag_rows = (
            await db.execute(
                select(Channel.tags)
                .where(Channel.is_archived.is_(False), playable)
                .order_by(Channel.popularity.desc())
                .limit(3000)
            )
        ).scalars().all()

        counter: Counter = Counter()
        for tags in tag_rows:
            counter.update(t for t in (tags or []) if len(t) > 2)

        top_countries = (
            await db.execute(
                select(Country.slug, Country.name_uz, Country.flag_emoji, Country.radio_count)
                .where(Country.radio_count > 0)
                .order_by(Country.radio_count.desc())
                .limit(6)
            )
        ).all()

        return {
            "stations": stations,
            "countries": countries,
            "top_genres": [
                {"tag": tag, "count": count} for tag, count in counter.most_common(10)
            ],
            "top_countries": [
                {
                    "slug": row.slug,
                    "name_uz": row.name_uz,
                    "flag_emoji": row.flag_emoji,
                    "radio_count": row.radio_count,
                }
                for row in top_countries
            ],
        }

    return await cached_json(redis, "stats:home", STATS_TTL, produce)


@router.get("/random")
async def random_station(
    response: Response,
    tag: str | None = Query(None, max_length=50),
    db: AsyncSession = Depends(get_db),
):
    """Tasodifiy ishlaydigan stansiya.

    Javobda imzolangan play_url bor — keshlanmaydi.
    """
    response.headers["Cache-Control"] = "private, no-store"

    filters = [
        Channel.is_archived.is_(False),
        Channel.type == "radio",
        _playable_exists(),
    ]
    if tag:
        filters.append(Channel.tags.contains([tag.lower()]))

    # TABLESAMPLE o'rniga: mashhur 500 tadan tasodifiy tanlaymiz. Shu bilan
    # ham tezlik saqlanadi, ham foydalanuvchi sifatsiz stansiyaga tushmaydi.
    candidates = (
        await db.execute(
            select(Channel.id)
            .where(*filters)
            .order_by(Channel.popularity.desc())
            .limit(500)
        )
    ).scalars().all()

    if not candidates:
        raise HTTPException(status_code=404, detail="Mos stansiya topilmadi")

    channel = (
        await db.execute(
            select(Channel)
            .options(selectinload(Channel.streams))
            .where(Channel.id == random.choice(candidates))
        )
    ).scalar_one_or_none()

    simple = to_simple(channel) if channel else None
    if not simple:
        raise HTTPException(status_code=404, detail="Mos stansiya topilmadi")

    country_iso2 = (
        await db.execute(
            select(ChannelCountry.country_iso2)
            .where(ChannelCountry.channel_id == channel.id)
            .limit(1)
        )
    ).scalar_one_or_none()

    payload = simple.model_dump()
    payload["country_iso2"] = country_iso2
    return payload
