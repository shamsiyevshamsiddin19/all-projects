"""Kanal va davlat bo'yicha qidiruv."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.channel import Channel
from app.models.country import Country
from app.models.stream import Stream
from app.routers.channels import MIN_PLAYABLE_SCORE, to_simple
from app.schemas.country import CountrySimple

router = APIRouter(prefix="/search", tags=["Search"])

# Trigram o'xshashligi chegarasi: pastroq qiymat ko'proq (lekin shovqinli) natija
SIMILARITY_THRESHOLD = 0.15


@router.get("")
async def search(
    response: Response,
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    # Natijada imzolangan play_url bor
    response.headers["Cache-Control"] = "private, no-store"

    term = q.strip()
    pattern = f"%{term.lower()}%"

    countries = (
        await db.execute(
            select(Country)
            .where(
                or_(
                    Country.name_en.ilike(pattern),
                    Country.name_uz.ilike(pattern),
                    func.lower(Country.iso2) == term.lower(),
                )
            )
            .order_by(desc(Country.radio_count))
            .limit(5)
        )
    ).scalars().all()

    # Trigram o'xshashligi bo'yicha tartiblash — ix_channels_name_trgm
    # GIN indeksidan foydalanadi. Oldin faqat ilike '%...%' ishlatilardi va
    # har qidiruvda butun jadval skanerlanardi.
    similarity = func.similarity(Channel.name, term)

    has_playable = (
        select(Stream.channel_id)
        .where(
            Stream.channel_id == Channel.id,
            Stream.is_active.is_(True),
            Stream.score > MIN_PLAYABLE_SCORE,
            Stream.is_geo_blocked.is_(False),
        )
        .exists()
    )

    channels = (
        await db.execute(
            select(Channel)
            .options(selectinload(Channel.streams))
            .where(
                Channel.is_archived.is_(False),
                has_playable,
                or_(
                    Channel.name.ilike(pattern),
                    similarity > SIMILARITY_THRESHOLD,
                ),
            )
            .order_by(desc(similarity), desc(Channel.popularity))
            .limit(limit)
        )
    ).scalars().unique().all()

    stations = [simple for simple in (to_simple(ch) for ch in channels) if simple]

    return {
        "query": term,
        "countries": [CountrySimple.model_validate(c) for c in countries],
        "stations": stations,
    }
