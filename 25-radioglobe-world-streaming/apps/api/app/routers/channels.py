"""Kanallar ro'yxati va tafsiloti."""

import base64
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.channel import Channel, ChannelCountry
from app.models.country import Country
from app.models.stream import Stream
from app.schemas.channel import ChannelDetail, ChannelListResponse, ChannelSimple
from app.schemas.stream import StreamInfo
from app.services.token_service import build_play_url

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Channels"])

# Shu balldan pastdagi oqimlar foydalanuvchiga umuman ko'rsatilmaydi
MIN_PLAYABLE_SCORE = 20


def stream_info(stream: Stream) -> StreamInfo:
    return StreamInfo(
        id=stream.id,
        format=stream.format or "mp3",
        bitrate=stream.bitrate,
        is_https=stream.is_https,
        needs_proxy=stream.needs_proxy,
        score=stream.score,
        play_url=build_play_url(stream),
    )


def playable_streams(channel: Channel) -> list[Stream]:
    """Kanalning ijro etsa bo'ladigan oqimlari — yaxshisidan boshlab."""
    streams = [
        s for s in channel.streams
        if s.is_active and s.score > MIN_PLAYABLE_SCORE and not s.is_geo_blocked
    ]
    return sorted(streams, key=lambda s: (s.priority, -s.score))


def to_simple(channel: Channel) -> Optional[ChannelSimple]:
    """Ijro etib bo'lmaydigan kanal uchun None — u ro'yxatga tushmaydi."""
    streams = playable_streams(channel)
    if not streams:
        return None

    infos = [stream_info(s) for s in streams]
    return ChannelSimple(
        id=channel.id,
        type=channel.type,
        slug=channel.slug,
        name=channel.name,
        logo_url=channel.logo_url,
        tags=channel.tags or [],
        languages=channel.languages or [],
        bitrate=channel.bitrate_max,
        score=infos[0].score,
        primary_stream=infos[0],
        # Birinchi oqim ishlamasa frontend zaxiraga o'tadi
        fallback_streams=infos[1:4],
    )


def _encode_cursor(payload: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(payload, default=str).encode()
    ).decode().rstrip("=")


def _decode_cursor(cursor: str) -> Optional[dict[str, Any]]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        return json.loads(base64.urlsafe_b64decode(padded).decode())
    except Exception:
        return None


# Tartiblash ustunlari: (asosiy ustun, yo'nalish). id har doim tiebreaker —
# busiz bir xil qiymatli qatorlar sahifalar orasida takrorlanadi yoki tushib qoladi.
_SORTS = {
    "popular": (Channel.popularity, "desc"),
    "name": (Channel.name, "asc"),
    "bitrate": (Channel.bitrate_max, "desc"),
}


def _apply_cursor(query, cursor: Optional[str], sort_column, direction: str):
    """Keyset paginatsiya sharti.

    OFFSET ishlatilmaydi: u katta ro'yxatlarda sekin va yangi yozuv
    qo'shilganda sahifalar siljib, element takrorlanadi yoki tushib qoladi.
    """
    if not cursor:
        return query
    decoded = _decode_cursor(cursor)
    if not decoded or "v" not in decoded or "id" not in decoded:
        return query

    last_value, last_id = decoded["v"], decoded["id"]
    if last_value is None:
        return query.where(Channel.id > last_id)
    if direction == "desc":
        return query.where(
            or_(
                sort_column < last_value,
                and_(sort_column == last_value, Channel.id > last_id),
            )
        )
    return query.where(
        or_(
            sort_column > last_value,
            and_(sort_column == last_value, Channel.id > last_id),
        )
    )


@router.get("/countries/{slug}/channels", response_model=ChannelListResponse)
async def list_country_channels(
    slug: str,
    response: Response,
    type: str = Query("radio", pattern="^(radio|tv)$"),
    sort: str = Query("popular", pattern="^(popular|name|bitrate)$"),
    tag: Optional[str] = Query(None, max_length=50),
    lang: Optional[str] = Query(None, max_length=50),
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Javobda imzolangan play_url bor — umumiy keshlarga tushmasligi kerak
    response.headers["Cache-Control"] = "private, no-store"

    country = (
        await db.execute(select(Country).where(Country.slug == slug))
    ).scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Davlat topilmadi")

    # Faqat ijro etsa bo'ladigan oqimi bor kanallar
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

    base_filters = [
        ChannelCountry.country_iso2 == country.iso2,
        Channel.type == type,
        Channel.is_archived.is_(False),
        has_playable,
    ]
    if tag:
        # JSONB `@>` — GIN indeksdan foydalanadi
        base_filters.append(Channel.tags.contains([tag.lower()]))
    if lang:
        base_filters.append(Channel.languages.contains([lang.lower()]))

    # Umumiy son — alohida COUNT. Oldin `total` sahifadagi elementlar soniga
    # teng edi va foydalanuvchiga noto'g'ri raqam ko'rsatilardi.
    total = (
        await db.execute(
            select(func.count(func.distinct(Channel.id)))
            .select_from(Channel)
            .join(ChannelCountry, ChannelCountry.channel_id == Channel.id)
            .where(and_(*base_filters))
        )
    ).scalar() or 0

    sort_column, direction = _SORTS[sort]
    order = [
        desc(sort_column).nulls_last() if direction == "desc" else asc(sort_column),
        asc(Channel.id),
    ]

    query = (
        select(Channel)
        .options(selectinload(Channel.streams))  # N+1 ni yo'q qiladi
        .join(ChannelCountry, ChannelCountry.channel_id == Channel.id)
        .where(and_(*base_filters))
        .order_by(*order)
    )

    query = _apply_cursor(query, cursor, sort_column, direction)

    # Bitta ortiqcha qator — keyingi sahifa bor-yo'qligini bilish uchun
    rows = (await db.execute(query.limit(limit + 1))).scalars().unique().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [simple for simple in (to_simple(ch) for ch in rows) if simple]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = _encode_cursor({
            "v": getattr(last, sort_column.key),
            "id": last.id,
        })

    return ChannelListResponse(total=total, items=items, next_cursor=next_cursor)


@router.get("/channels", response_model=ChannelListResponse)
async def list_channels_by_tag(
    response: Response,
    tag: str = Query(..., min_length=2, max_length=50, description="Janr (tag)"),
    sort: str = Query("popular", pattern="^(popular|name|bitrate)$"),
    limit: int = Query(60, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Janr bo'yicha global ro'yxat (barcha davlatlar kesimida).

    Davlat sahifasidagi filtrdan farqi: bu yerda davlat cheklovi yo'q, shuning
    uchun "jazz radio" kabi so'rovlar uchun alohida sahifa yasash mumkin.
    """
    response.headers["Cache-Control"] = "private, no-store"

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

    base_filters = [
        Channel.type == "radio",
        Channel.is_archived.is_(False),
        Channel.tags.contains([tag.lower()]),
        has_playable,
    ]

    total = (
        await db.execute(
            select(func.count(Channel.id)).where(and_(*base_filters))
        )
    ).scalar() or 0

    sort_column, direction = _SORTS[sort]
    order = [
        desc(sort_column).nulls_last() if direction == "desc" else asc(sort_column),
        asc(Channel.id),
    ]

    query = (
        select(Channel)
        .options(selectinload(Channel.streams))
        .where(and_(*base_filters))
        .order_by(*order)
    )
    query = _apply_cursor(query, cursor, sort_column, direction)

    rows = (await db.execute(query.limit(limit + 1))).scalars().unique().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [simple for simple in (to_simple(ch) for ch in rows) if simple]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = _encode_cursor({"v": getattr(last, sort_column.key), "id": last.id})

    return ChannelListResponse(total=total, items=items, next_cursor=next_cursor)


@router.get("/channels/{slug}", response_model=ChannelDetail)
async def get_channel_detail(
    slug: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"

    channel = (
        await db.execute(
            select(Channel)
            .options(selectinload(Channel.streams), selectinload(Channel.country_links))
            .where(Channel.slug == slug, Channel.is_archived.is_(False))
        )
    ).scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal topilmadi")

    # Tafsilot sahifasida ham filtr qo'llanadi — oldin bu yerda filtr yo'q edi
    # va o'lik oqimlar qaytarilardi
    streams = playable_streams(channel)
    if not streams:
        raise HTTPException(status_code=404, detail="Bu kanalda faol oqim yo'q")

    infos = [stream_info(s) for s in streams]
    primary_country = next(
        (link.country_iso2 for link in channel.country_links if link.is_primary),
        next((link.country_iso2 for link in channel.country_links), None),
    )

    return ChannelDetail(
        id=channel.id,
        type=channel.type,
        slug=channel.slug,
        name=channel.name,
        logo_url=channel.logo_url,
        homepage=channel.homepage,
        tags=channel.tags or [],
        languages=channel.languages or [],
        bitrate=channel.bitrate_max,
        score=infos[0].score,
        primary_stream=infos[0],
        fallback_streams=infos[1:4],
        popularity=channel.popularity,
        streams=infos,
        country_iso2=primary_country,
    )
