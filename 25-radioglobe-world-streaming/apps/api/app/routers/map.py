from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.country import Country
import json
from pathlib import Path
from typing import Dict, Any

router = APIRouter(prefix="/map", tags=["Map"])

GEOJSON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "countries.geojson"

@router.get("/counts")
async def get_map_counts(db: AsyncSession = Depends(get_db)):
    """
    Lightweight endpoint returning live station counts for each country (for instant choropleth updates).
    """
    result = await db.execute(select(Country.iso2, Country.radio_count, Country.tv_count))
    rows = result.all()
    
    counts: Dict[str, Dict[str, int]] = {}
    for iso2, radio_cnt, tv_cnt in rows:
        counts[iso2] = {
            "radio": radio_cnt,
            "tv": tv_cnt
        }
    return counts


@router.get("/countries.geojson")
async def get_countries_geojson(response: Response, db: AsyncSession = Depends(get_db)):
    """
    Returns world boundaries GeoJSON enriched with country metadata and station counts.
    Cached for 1 hour with stale-while-revalidate.
    """
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    
    if not GEOJSON_PATH.exists():
        # Fallback empty collection if not yet seeded
        return {"type": "FeatureCollection", "features": []}

    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    # Fetch latest counts from DB
    result = await db.execute(select(Country.m49, Country.iso2, Country.slug, Country.name_uz, Country.name_en, Country.radio_count, Country.tv_count))
    country_map = {
        row.m49: {
            "iso2": row.iso2,
            "slug": row.slug,
            "name_uz": row.name_uz,
            "name_en": row.name_en,
            "radio_count": row.radio_count,
            "tv_count": row.tv_count,
        }
        for row in result.all()
    }

    # Enrich features
    for feature in geojson.get("features", []):
        m49 = feature.get("properties", {}).get("m49")
        if m49 in country_map:
            feature["properties"].update(country_map[m49])

    return geojson
