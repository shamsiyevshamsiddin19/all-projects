"""radio-browser.info dan stansiyalarni olib kelish (ingest).

Oldingi versiyadagi muammolar va ularning yechimi:
  * Faqat ~450 stansiya olinardi  → endi har davlat bo'yicha yuriladi
  * Mavjud kanal yangilanmasdi    → UPSERT (nom, logo, popularity yangilanadi)
  * Qidiruv slug bo'yicha edi     → endi radiobrowser_uuid bo'yicha (barqaror)
  * Yo'qolgan stansiya qolib ketardi → endi is_archived=True qilinadi
  * Davlat hisobi 250 ta UPDATE   → endi bitta GROUP BY
"""

import asyncio
import logging
import os
import re
import sys
from typing import Optional
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))

from app.config import settings  # noqa: E402
from app.models.channel import Channel, ChannelCountry  # noqa: E402
from app.models.country import Country  # noqa: E402
from app.models.stream import Stream  # noqa: E402

logger = logging.getLogger("ingest")

MAX_PER_COUNTRY = int(os.getenv("INGEST_MAX_PER_COUNTRY", "500"))
REQUEST_DELAY = float(os.getenv("INGEST_REQUEST_DELAY", "0.5"))  # manbaga hurmat
HTTP_TIMEOUT = 30.0

# radio-browser codec qiymatlarini bizning format'ga moslash
CODEC_MAP = {
    "mp3": "mp3", "aac": "aac", "aac+": "aac", "aacp": "aac",
    "ogg": "ogg", "vorbis": "ogg", "opus": "ogg",
    "flac": "flac", "hls": "hls", "unknown": "mp3",
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "station"


def clean_name(raw: str) -> str:
    """Stansiya nomidagi shovqinni tozalaydi."""
    name = (raw or "").strip()
    name = re.sub(r"\s+", " ", name)
    # Ko'p stansiyalar nomiga "- LIVE", "128kbps", "|||" kabi shovqin qo'shadi
    name = re.sub(r"\s*[\|\-–]{1,3}\s*(live|online|stream|hq|\d+\s*kbps)\s*$", "", name, flags=re.I)
    return name.strip(" -|–") or raw.strip()


def parse_list(raw: str, limit: int) -> list[str]:
    if not raw:
        return []
    seen, out = set(), []
    for part in str(raw).split(","):
        value = part.strip().lower()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
        if len(out) >= limit:
            break
    return out


async def fetch_json(client: httpx.AsyncClient, path: str):
    """Mirrorlarni navbat bilan sinab ko'radi."""
    for mirror in settings.RADIO_BROWSER_MIRRORS:
        try:
            res = await client.get(f"https://{mirror}/json/{path}")
            if res.status_code == 200:
                return res.json()
            logger.warning("%s → HTTP %s", mirror, res.status_code)
        except Exception as exc:
            logger.warning("Mirror ishlamadi (%s): %s", mirror, exc)
    return []


async def fetch_all_stations(iso_codes: list[str]) -> list[dict]:
    """Har bir davlat uchun eng mashhur stansiyalarni oladi."""
    headers = {"User-Agent": settings.USER_AGENT}
    stations: dict[str, dict] = {}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=headers) as client:
        for index, iso2 in enumerate(iso_codes, start=1):
            path = (
                f"stations/bycountrycodeexact/{iso2}"
                f"?hidebroken=true&order=clickcount&reverse=true&limit={MAX_PER_COUNTRY}"
            )
            rows = await fetch_json(client, path)
            added = 0
            for row in rows or []:
                uuid = row.get("stationuuid")
                if uuid and uuid not in stations:
                    stations[uuid] = row
                    added += 1
            if added:
                logger.info("[%3d/%d] %s → %d stansiya", index, len(iso_codes), iso2, added)
            # Manbaga hurmat: so'rovlarni zichlashtirmaymiz
            await asyncio.sleep(REQUEST_DELAY)

    return list(stations.values())


def normalize(row: dict, valid_iso: set[str]) -> Optional[dict]:
    """Xom yozuvni bizning modelga moslaydi. Yaroqsiz bo'lsa None."""
    iso2 = (row.get("countrycode") or "").upper().strip()
    if iso2 not in valid_iso:
        return None

    name = clean_name(row.get("name") or "")
    if not name:
        return None

    url = (row.get("url") or "").strip()
    url_resolved = (row.get("url_resolved") or "").strip() or None
    effective = url_resolved or url
    if not effective.startswith(("http://", "https://")):
        return None

    uuid = row.get("stationuuid")
    if not uuid:
        return None

    codec = (row.get("codec") or "mp3").strip().lower()
    bitrate = row.get("bitrate") or 0

    logo = (row.get("favicon") or "").strip() or None
    # HTTP logo HTTPS sahifada bloklanadi — bunday logoni saqlamaymiz
    if logo and not logo.startswith("https://"):
        logo = None

    return {
        "uuid": uuid,
        "iso2": iso2,
        "name": name,
        "slug": f"{slugify(name)}-{uuid[:6]}",
        "logo_url": logo,
        "homepage": (row.get("homepage") or "").strip() or None,
        "languages": parse_list(row.get("language"), 3),
        "tags": parse_list(row.get("tags"), 5),
        "bitrate": bitrate if 0 < bitrate < 2000 else None,
        "format": CODEC_MAP.get(codec, "mp3"),
        "popularity": int(row.get("votes") or 0) + int(row.get("clickcount") or 0),
        "url": url or effective,
        "url_resolved": url_resolved,
        "is_https": effective.startswith("https://"),
    }


async def ingest_stations() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("🚀 radio-browser ingest boshlandi")

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        iso_codes = sorted(
            (await session.execute(select(Country.iso2).where(func.length(Country.iso2) == 2)))
            .scalars()
            .all()
        )

    if not iso_codes:
        raise SystemExit("Davlatlar jadvali bo'sh. Avval: python seed_countries.py")

    raw_rows = await fetch_all_stations(iso_codes)
    logger.info("Jami %d ta noyob stansiya olindi", len(raw_rows))

    valid_iso = set(iso_codes)
    normalized = [n for n in (normalize(r, valid_iso) for r in raw_rows) if n]
    logger.info("Normalizatsiyadan o'tdi: %d", len(normalized))

    if not normalized:
        logger.error("Yaroqli stansiya topilmadi — baza o'zgartirilmaydi")
        await engine.dispose()
        return

    created = updated = archived = 0
    now = datetime.now(timezone.utc)

    async with session_factory() as session:
        existing_channels = {}
        for channel in (
            await session.execute(select(Channel).where(Channel.source == "radio-browser"))
        ).scalars().all():
            uuid = (channel.external_ids or {}).get("radiobrowser_uuid")
            if uuid:
                existing_channels[uuid] = channel

        seen_uuids = set()

        for item in normalized:
            seen_uuids.add(item["uuid"])
            channel = existing_channels.get(item["uuid"])

            if channel is None:
                channel = Channel(
                    type="radio",
                    name=item["name"],
                    slug=item["slug"],
                    logo_url=item["logo_url"],
                    homepage=item["homepage"],
                    languages=item["languages"],
                    tags=item["tags"],
                    bitrate_max=item["bitrate"],
                    source="radio-browser",
                    external_ids={"radiobrowser_uuid": item["uuid"]},
                    popularity=item["popularity"],
                    is_archived=False,
                )
                session.add(channel)
                await session.flush()

                session.add(ChannelCountry(
                    channel_id=channel.id,
                    country_iso2=item["iso2"],
                    is_primary=True,
                ))
                session.add(Stream(
                    channel_id=channel.id,
                    url=item["url"],
                    url_resolved=item["url_resolved"],
                    format=item["format"],
                    bitrate=item["bitrate"],
                    is_https=item["is_https"],
                    sends_cors=False,
                    needs_proxy=True,
                    # Hali tekshirilmagan: health checker tasdiqlagunicha o'rtacha ball.
                    # Oldin 95 qo'yilardi — natijada tekshirilmagan o'lik oqimlar
                    # "ishonchli" bo'lib ko'rinardi.
                    score=50,
                    is_active=True,
                ))
                created += 1
                continue

            # Mavjud kanalni yangilash
            changed = False
            for field, value in (
                ("name", item["name"]),
                ("logo_url", item["logo_url"]),
                ("homepage", item["homepage"]),
                ("languages", item["languages"]),
                ("tags", item["tags"]),
                ("bitrate_max", item["bitrate"]),
                ("popularity", item["popularity"]),
            ):
                if value is not None and getattr(channel, field) != value:
                    setattr(channel, field, value)
                    changed = True

            if channel.is_archived:
                channel.is_archived = False
                changed = True

            stream = (
                await session.execute(
                    select(Stream).where(Stream.channel_id == channel.id).limit(1)
                )
            ).scalar_one_or_none()

            if stream is None:
                session.add(Stream(
                    channel_id=channel.id,
                    url=item["url"],
                    url_resolved=item["url_resolved"],
                    format=item["format"],
                    bitrate=item["bitrate"],
                    is_https=item["is_https"],
                    needs_proxy=True,
                    score=50,
                    is_active=True,
                ))
                changed = True
            elif item["url_resolved"] and stream.url_resolved != item["url_resolved"]:
                stream.url_resolved = item["url_resolved"]
                stream.is_https = item["is_https"]
                changed = True

            if changed:
                channel.updated_at = now
                updated += 1

        # Manbadan yo'qolganlarni arxivlash (O'CHIRMAYMIZ: manbada vaqtinchalik
        # xato bo'lishi mumkin, o'chirilsa slug va statistika ham yo'qoladi)
        for uuid, channel in existing_channels.items():
            if uuid not in seen_uuids and not channel.is_archived:
                channel.is_archived = True
                archived += 1

        await session.commit()

    # Davlat hisoblagichlari — bitta GROUP BY (oldin 250 ta alohida UPDATE edi).
    # Faqat arxivlanmagan, faol va ishlaydigan oqimi bor kanallar sanaladi,
    # shunda globusdagi raqam ro'yxatdagi kanallar soni bilan mos keladi.
    async with session_factory() as session:
        counts_stmt = (
            select(ChannelCountry.country_iso2, func.count(func.distinct(Channel.id)))
            .select_from(ChannelCountry)
            .join(Channel, Channel.id == ChannelCountry.channel_id)
            .join(Stream, Stream.channel_id == Channel.id)
            .where(
                Channel.is_archived.is_(False),
                Channel.type == "radio",
                Stream.is_active.is_(True),
            )
            .group_by(ChannelCountry.country_iso2)
        )
        counts = dict((await session.execute(counts_stmt)).all())

        await session.execute(update(Country).values(radio_count=0))
        for iso2, count in counts.items():
            await session.execute(
                update(Country).where(Country.iso2 == iso2).values(radio_count=count)
            )
        await session.commit()

    await engine.dispose()
    logger.info(
        "✅ Ingest yakunlandi — yangi: %d, yangilandi: %d, arxivlandi: %d, "
        "kanali bor davlatlar: %d",
        created, updated, archived, len(counts),
    )


if __name__ == "__main__":
    asyncio.run(ingest_stations())
