"""Globus uchun geometriya va hisoblagichlar."""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.models.country import Country
from app.services.cache import cached_json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/map", tags=["Map"])

GEOJSON_PATH = Path(__file__).resolve().parents[2] / "data" / "countries.geojson"

# Geometriya o'zgarmas — diskdan BIR MARTA o'qiladi.
# Oldin har so'rovda 200 KB fayl ochilib, json.load bilan parse qilinardi.
# Bu async handler ichidagi bloklovchi I/O edi va butun event loop'ni
# to'xtatib turardi.
_geojson_cache: dict[str, Any] | None = None


def _load_geojson() -> dict[str, Any]:
    global _geojson_cache
    if _geojson_cache is None:
        if not GEOJSON_PATH.exists():
            logger.error("countries.geojson topilmadi: %s", GEOJSON_PATH)
            _geojson_cache = {"type": "FeatureCollection", "features": []}
        else:
            with GEOJSON_PATH.open("r", encoding="utf-8") as fh:
                _geojson_cache = json.load(fh)
            logger.info(
                "Globus geometriyasi yuklandi: %d ta davlat",
                len(_geojson_cache.get("features", [])),
            )
    return _geojson_cache


async def _fetch_counts(db: AsyncSession) -> dict[str, dict[str, int]]:
    rows = (
        await db.execute(
            select(Country.iso2, Country.m49, Country.radio_count, Country.tv_count)
        )
    ).all()
    return {
        row.iso2: {"m49": row.m49, "radio": row.radio_count, "tv": row.tv_count}
        for row in rows
    }


@router.get("/counts")
async def get_map_counts(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Faqat raqamlar — choropleth'ni yangilash uchun yengil endpoint."""
    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=3600"
    counts = await cached_json(redis, "map:counts", 600, lambda: _fetch_counts(db))
    return {iso2: {"radio": v["radio"], "tv": v["tv"]} for iso2, v in counts.items()}


@router.get("/countries.geojson")
async def get_countries_geojson(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Globus uchun chegaralar + jonli stansiya soni.

    Geometriya statik, hisoblagichlar bazadan keladi. Bog'lanish M49 raqamli
    kodi bo'yicha: Natural Earth ma'lumotida ISO_A2 ba'zi davlatlarda "-99"
    bo'lib chiqadi va ular bog'lanmay qolardi.
    """
    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=86400"
    # Content-Type QO'LDA qo'yilmaydi: FastAPI o'zi "application/json" qo'yadi va
    # ikkitasi birikib "application/json, application/geo+json" degan buzuq
    # qiymat hosil bo'lardi — MapLibre bunday javobni parse qila olmaydi.

    geojson = _load_geojson()
    counts = await cached_json(redis, "map:counts", 600, lambda: _fetch_counts(db))
    by_m49 = {v["m49"]: (v["radio"], v["tv"]) for v in counts.values()}

    features = []
    for feature in geojson.get("features", []):
        props = dict(feature.get("properties", {}))
        radio, tv = by_m49.get(props.get("m49"), (0, 0))
        props["radio_count"] = radio
        props["tv_count"] = tv
        features.append({**feature, "properties": props})

    return {"type": "FeatureCollection", "features": features}
