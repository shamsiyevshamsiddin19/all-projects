import asyncio
import json
import re
import sys
from pathlib import Path
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, func

sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))
from app.config import settings
from app.models.country import Country
from app.models.channel import Channel, ChannelCountry
from app.models.stream import Stream

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-') or "station"

async def fetch_stations_from_radio_browser(endpoint: str, timeout: float = 15.0):
    headers = {"User-Agent": settings.USER_AGENT}
    for mirror in settings.RADIO_BROWSER_MIRRORS:
        url = f"https://{mirror}/json/{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            print(f"Failed to connect to mirror {mirror}: {e}")
            continue
    return []

async def ingest_stations():
    print("🚀 Radio-Browser Ingest boshlandi...")
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 1. Fetch stations: Uzbekistan priority, then top globally, then top by country
    stations_to_ingest = []
    
    # Priority: Uzbekistan
    print("Fetching Uzbekistan stations...")
    uz_stations = await fetch_stations_from_radio_browser("stations/bycountrycodeexact/UZ")
    stations_to_ingest.extend(uz_stations)
    print(f"Uzbekistan stations: {len(uz_stations)}")

    # Top clicked
    print("Fetching top clicked stations...")
    top_clicks = await fetch_stations_from_radio_browser("stations/topclick/150")
    stations_to_ingest.extend(top_clicks)

    # Top voted
    print("Fetching top voted stations...")
    top_votes = await fetch_stations_from_radio_browser("stations/topvote/150")
    stations_to_ingest.extend(top_votes)

    # De-duplicate by stationuuid
    seen_uuids = set()
    unique_stations = []
    for s in stations_to_ingest:
        uuid = s.get("stationuuid")
        if uuid and uuid not in seen_uuids:
            seen_uuids.add(uuid)
            unique_stations.append(s)

    print(f"Total unique stations to ingest: {len(unique_stations)}")

    async with session_factory() as session:
        # Load existing country ISO codes
        countries_res = await session.execute(select(Country.iso2))
        valid_iso_codes = set(countries_res.scalars().all())

        imported_count = 0
        for s in unique_stations:
            raw_country = (s.get("countrycode") or "").upper().strip()
            if raw_country not in valid_iso_codes:
                continue

            name = (s.get("name") or "").strip()
            if not name:
                continue

            stream_url = s.get("url_resolved") or s.get("url")
            if not stream_url or not stream_url.startswith(("http://", "https://")):
                continue

            uuid = s.get("stationuuid")
            slug_base = slugify(name)
            # Ensure unique slug
            slug = f"{slug_base}-{uuid[:6]}"

            # Parse tags
            raw_tags = s.get("tags") or ""
            tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()][:5]

            # Parse languages
            raw_lang = s.get("language") or ""
            languages = [l.strip().lower() for l in raw_lang.split(",") if l.strip()][:3]

            bitrate = s.get("bitrate") or 128
            codec = (s.get("codec") or "mp3").lower()
            logo_url = s.get("favicon") or None
            homepage = s.get("homepage") or None
            popularity = (s.get("votes") or 0) + (s.get("clickcount") or 0)

            # Check if channel exists by external UUID
            existing_ch_res = await session.execute(
                select(Channel).where(Channel.slug == slug)
            )
            channel = existing_ch_res.scalar_one_or_none()

            if not channel:
                channel = Channel(
                    type="radio",
                    name=name,
                    slug=slug,
                    logo_url=logo_url,
                    homepage=homepage,
                    languages=languages,
                    tags=tags,
                    bitrate_max=bitrate,
                    source="radio-browser",
                    external_ids={"radiobrowser_uuid": uuid},
                    popularity=popularity,
                    is_archived=False
                )
                session.add(channel)
                await session.flush()

                # Link to country
                link = ChannelCountry(
                    channel_id=channel.id,
                    country_iso2=raw_country,
                    is_primary=True
                )
                session.add(link)

                # Create stream
                is_https = stream_url.startswith("https://")
                stream = Stream(
                    channel_id=channel.id,
                    url=s.get("url"),
                    url_resolved=s.get("url_resolved"),
                    format=codec,
                    bitrate=bitrate,
                    is_https=is_https,
                    sends_cors=False,
                    needs_proxy=True,
                    score=95,
                    is_active=True
                )
                session.add(stream)
                imported_count += 1

        await session.commit()
        print(f"Successfully imported {imported_count} stations!")

        # Update country radio counts
        print("Updating country radio counts...")
        for iso2 in valid_iso_codes:
            cnt_res = await session.execute(
                select(func.count(ChannelCountry.channel_id))
                .where(ChannelCountry.country_iso2 == iso2)
            )
            count = cnt_res.scalar() or 0
            await session.execute(
                update(Country).where(Country.iso2 == iso2).values(radio_count=count)
            )
        await session.commit()
        print("Country station counts successfully updated!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(ingest_stations())
