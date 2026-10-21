"""Davlatlar ma'lumotini va globus GeoJSON'ini yagona manbadan quradi.

Chiqish:
  1. apps/worker/data/countries.json   — bazani to'ldirish uchun (seed)
  2. apps/api/data/countries.geojson   — API boyitib beradigan geometriya
  3. apps/web/public/countries.geojson — zaxira (API ishlamasa)

Nega bitta skript: oldin seed ro'yxati qo'lda yozilgan (40 davlat), GeoJSON esa
alohida qurilardi — natijada globusdagi 177 davlatdan 137 tasi bazada yo'q edi
va bosilganda 404 berardi. Endi ikkalasi ham shu yerdan chiqadi.
"""

import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

import pycountry

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data.country_names_uz import (  # noqa: E402
    CONTINENT_BY_ISO2,
    CONTINENT_UZ,
    COUNTRY_NAMES_UZ,
    NO_ISO_TERRITORIES_UZ,
)

SOURCE_URL = (
    "https://raw.githubusercontent.com/datasets/"
    "geo-boundaries-world-110m/master/countries.geojson"
)

ROOT = Path(__file__).resolve().parent.parent
OUT_SEED = Path(__file__).resolve().parent / "data" / "countries.json"
OUT_API = ROOT / "api" / "data" / "countries.geojson"
OUT_WEB = ROOT / "web" / "public" / "countries.geojson"

COORD_PRECISION = 2  # ~1.1 km — globus masshtabi uchun yetarli

FLAG_OFFSET = 0x1F1E6 - ord("A")


def flag_emoji(iso2: str) -> str:
    if len(iso2) != 2 or not iso2.isalpha():
        return ""
    return "".join(chr(ord(ch) + FLAG_OFFSET) for ch in iso2.upper())


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def round_coords(value, precision=COORD_PRECISION):
    if isinstance(value, float):
        return round(value, precision)
    if isinstance(value, list):
        return [round_coords(v, precision) for v in value]
    return value


def _rings(geometry: dict) -> list[list]:
    """Geometriyadagi barcha tashqi halqalarni qaytaradi."""
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if gtype == "Polygon":
        return [coords[0]] if coords else []
    if gtype == "MultiPolygon":
        return [poly[0] for poly in coords if poly]
    return []


def _ring_area(ring: list) -> float:
    """Shoelace formulasi — nisbiy kattalikni solishtirish uchun yetarli."""
    area = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def main_landmass_geometry(geometry: dict):
    """Eng katta quruqlik bo'lagi bo'yicha centroid va bbox.

    Nega eng kattasi: Rossiya, AQSH, Fiji va Yangi Zelandiya 180-meridianni
    kesib o'tadi. Butun geometriya bo'yicha bbox olinsa, u -180..180 ni qamrab
    oladi va `fitBounds` butun dunyoni ko'rsatib yuboradi. Eng katta bo'lak
    bo'yicha hisoblash bu muammoni butunlay chetlab o'tadi.
    """
    rings = _rings(geometry)
    if not rings:
        return None, None

    largest = max(rings, key=_ring_area)

    lons = [p[0] for p in largest]
    lats = [p[1] for p in largest]
    if not lons or not lats:
        return None, None

    bbox = [
        round(min(lons), 3), round(min(lats), 3),
        round(max(lons), 3), round(max(lats), 3),
    ]
    centroid = [
        round((bbox[0] + bbox[2]) / 2, 4),
        round((bbox[1] + bbox[3]) / 2, 4),
    ]
    return centroid, bbox


def resolve_codes(props: dict):
    """iso2, iso3, m49 ni aniqlaydi.

    Natural Earth'da `iso_a2` ba'zan "-99" bo'ladi (nizoli hududlar), shuning
    uchun avval ishonchliroq `iso_a3` orqali pycountry'dan izlaymiz.
    """
    iso3 = (props.get("iso_a3") or "").strip().upper()
    iso2 = (props.get("iso_a2") or "").strip().upper()

    record = None
    if iso3 and iso3 != "-99":
        record = pycountry.countries.get(alpha_3=iso3)
    if record is None and iso2 and iso2 != "-99":
        record = pycountry.countries.get(alpha_2=iso2)

    if record is not None:
        return record.alpha_2, record.alpha_3, int(record.numeric)

    # ISO kodi yo'q hudud (Kosovo, Shimoliy Kipr, Somalilend)
    adm = (props.get("adm0_a3") or props.get("sov_a3") or "").upper()
    fallback = {
        "CYN": ("CY-N", "CYN", 9001),
        "KOS": ("XK", "XKX", 9002),
        "SOL": ("SO-L", "SOL", 9003),
    }
    return fallback.get(adm)


def build():
    print(f"📥 Chegaralar yuklanmoqda: {SOURCE_URL}")
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "RadioGlobe/1.1"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    features_in = raw.get("features", [])
    print(f"   Manbada {len(features_in)} ta geometriya")

    seed = {}
    features_out = []
    used_slugs = set()
    skipped = []

    for feat in features_in:
        props = feat.get("properties", {})
        codes = resolve_codes(props)
        if not codes:
            skipped.append(props.get("name"))
            continue

        iso2, iso3, m49 = codes
        name_en = props.get("name_long") or props.get("name") or iso3
        name_uz = (
            COUNTRY_NAMES_UZ.get(iso2)
            or NO_ISO_TERRITORIES_UZ.get((props.get("adm0_a3") or "").upper())
            or name_en
        )

        slug = slugify(name_en)
        if slug in used_slugs:
            slug = f"{slug}-{iso2.lower()}"
        used_slugs.add(slug)

        continent_en = props.get("continent") or "Asia"
        geometry = feat.get("geometry") or {}
        centroid, bbox = main_landmass_geometry(geometry)

        seed[iso2] = {
            "iso2": iso2,
            "iso3": iso3,
            "m49": m49,
            "name_en": name_en,
            "name_uz": name_uz,
            "slug": slug,
            "continent": CONTINENT_UZ.get(continent_en)
            or CONTINENT_BY_ISO2.get(iso2)
            or continent_en,
            "flag_emoji": flag_emoji(iso2) if len(iso2) == 2 else "",
            "centroid_lat": centroid[1] if centroid else None,
            "centroid_lon": centroid[0] if centroid else None,
            "bbox": bbox,
        }

        geometry["coordinates"] = round_coords(geometry.get("coordinates"))
        features_out.append({
            "type": "Feature",
            # feature.id — MapLibre feature-state uchun barqaror kalit.
            # generateId ishlatilmaydi, chunki u har yuklashda o'zgaradi.
            "id": m49,
            "properties": {
                "m49": m49,
                "iso2": iso2,
                "slug": slug,       # click handler to'g'ridan-to'g'ri shuni ishlatadi
                "name_uz": name_uz,
                "name_en": name_en,
                "flag_emoji": seed[iso2]["flag_emoji"],
                "radio_count": 0,   # API jonli qiymat bilan almashtiradi
                "tv_count": 0,
            },
            "geometry": geometry,
        })

    # Globusda geometriyasi yo'q, lekin radiosi bo'lishi mumkin bo'lgan
    # davlatlarni ham bazaga qo'shamiz (Singapur, Malta, Bahrayn va h.k.)
    added_extra = 0
    for country in pycountry.countries:
        iso2 = country.alpha_2
        if iso2 in seed:
            continue
        name_en = country.name
        slug = slugify(name_en)
        if slug in used_slugs:
            slug = f"{slug}-{iso2.lower()}"
        used_slugs.add(slug)
        seed[iso2] = {
            "iso2": iso2,
            "iso3": country.alpha_3,
            "m49": int(country.numeric),
            "name_en": name_en,
            "name_uz": COUNTRY_NAMES_UZ.get(iso2, name_en),
            "slug": slug,
            # Geometriyasi yo'q bo'lsa ham qit'a ma'lum — aks holda
            # katalogda "Boshqa" guruhiga tushib qolardi
            "continent": CONTINENT_BY_ISO2.get(iso2, "Boshqa"),
            "flag_emoji": flag_emoji(iso2),
            "centroid_lat": None,
            "centroid_lon": None,
            "bbox": None,
        }
        added_extra += 1

    OUT_SEED.parent.mkdir(parents=True, exist_ok=True)
    OUT_SEED.write_text(
        json.dumps(
            sorted(seed.values(), key=lambda c: c["iso2"]),
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    geojson = {"type": "FeatureCollection", "features": features_out}
    payload = json.dumps(geojson, ensure_ascii=False, separators=(",", ":"))
    for out in (OUT_API, OUT_WEB):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")

    uz_named = sum(1 for c in seed.values() if c["iso2"] in COUNTRY_NAMES_UZ)
    print(f"✅ Seed: {len(seed)} davlat ({added_extra} tasi geometriyasiz)")
    print(f"   O'zbekcha nomlangan: {uz_named}")
    print(f"✅ GeoJSON: {len(features_out)} geometriya, {len(payload)/1024:.0f} KB")
    if skipped:
        print(f"ℹ️  Kod aniqlanmagani uchun o'tkazib yuborildi: {skipped}")


if __name__ == "__main__":
    build()
