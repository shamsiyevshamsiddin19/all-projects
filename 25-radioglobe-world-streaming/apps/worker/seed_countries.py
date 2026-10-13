import asyncio
import json
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Add apps/api to path for models
sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))
from app.config import settings
from app.models.country import Country

# Comprehensive dataset of world countries with ISO2, ISO3, M49, Uzbek/English names, flag emoji, centroid, bbox
COUNTRIES_DATA = [
    {"iso2": "UZ", "iso3": "UZB", "m49": 860, "name_uz": "O'zbekiston", "name_en": "Uzbekistan", "slug": "uzbekistan", "continent": "Asia", "flag_emoji": "🇺🇿", "centroid_lat": 41.3775, "centroid_lon": 64.5853, "bbox": [55.998, 37.185, 73.149, 45.571]},
    {"iso2": "KZ", "iso3": "KAZ", "m49": 398, "name_uz": "Qozog'iston", "name_en": "Kazakhstan", "slug": "kazakhstan", "continent": "Asia", "flag_emoji": "🇰🇿", "centroid_lat": 48.0196, "centroid_lon": 66.9237, "bbox": [46.493, 40.569, 87.315, 55.437]},
    {"iso2": "KG", "iso3": "KGZ", "m49": 417, "name_uz": "Qirg'iziston", "name_en": "Kyrgyzstan", "slug": "kyrgyzstan", "continent": "Asia", "flag_emoji": "🇰🇬", "centroid_lat": 41.2044, "centroid_lon": 74.7661, "bbox": [69.278, 39.172, 80.283, 43.267]},
    {"iso2": "TJ", "iso3": "TJK", "m49": 762, "name_uz": "Tojikiston", "name_en": "Tajikistan", "slug": "tajikistan", "continent": "Asia", "flag_emoji": "🇹🇯", "centroid_lat": 38.861, "centroid_lon": 71.2761, "bbox": [67.398, 36.673, 75.142, 41.042]},
    {"iso2": "TM", "iso3": "TKM", "m49": 795, "name_uz": "Turkmaniston", "name_en": "Turkmenistan", "slug": "turkmenistan", "continent": "Asia", "flag_emoji": "🇹🇲", "centroid_lat": 38.9697, "centroid_lon": 59.5563, "bbox": [52.448, 35.143, 66.69, 42.798]},
    {"iso2": "TR", "iso3": "TUR", "m49": 792, "name_uz": "Turkiya", "name_en": "Turkey", "slug": "turkey", "continent": "Asia", "flag_emoji": "🇹🇷", "centroid_lat": 38.9637, "centroid_lon": 35.2433, "bbox": [25.668, 35.817, 44.823, 42.107]},
    {"iso2": "AZ", "iso3": "AZE", "m49": 31, "name_uz": "Ozarbayjon", "name_en": "Azerbaijan", "slug": "azerbaijan", "continent": "Asia", "flag_emoji": "🇦🇿", "centroid_lat": 40.1431, "centroid_lon": 47.5769, "bbox": [44.773, 38.392, 50.375, 41.906]},
    {"iso2": "RU", "iso3": "RUS", "m49": 643, "name_uz": "Rossiya", "name_en": "Russia", "slug": "russia", "continent": "Europe", "flag_emoji": "🇷🇺", "centroid_lat": 61.524, "centroid_lon": 105.3188, "bbox": [19.639, 41.185, 180.0, 81.858]},
    {"iso2": "US", "iso3": "USA", "m49": 840, "name_uz": "AQSH", "name_en": "United States", "slug": "united-states", "continent": "North America", "flag_emoji": "🇺🇸", "centroid_lat": 37.0902, "centroid_lon": -95.7129, "bbox": [-124.848, 24.396, -66.885, 49.384]},
    {"iso2": "GB", "iso3": "GBR", "m49": 826, "name_uz": "Buyuk Britaniya", "name_en": "United Kingdom", "slug": "united-kingdom", "continent": "Europe", "flag_emoji": "🇬🇧", "centroid_lat": 55.3781, "centroid_lon": -3.436, "bbox": [-8.65, 49.864, 1.768, 60.861]},
    {"iso2": "DE", "iso3": "DEU", "m49": 276, "name_uz": "Germaniya", "name_en": "Germany", "slug": "germany", "continent": "Europe", "flag_emoji": "🇩🇪", "centroid_lat": 51.1657, "centroid_lon": 10.4515, "bbox": [5.866, 47.27, 15.042, 55.058]},
    {"iso2": "FR", "iso3": "FRA", "m49": 250, "name_uz": "Fransiya", "name_en": "France", "slug": "france", "continent": "Europe", "flag_emoji": "🇫🇷", "centroid_lat": 46.2276, "centroid_lon": 2.2137, "bbox": [-5.141, 41.334, 9.56, 51.089]},
    {"iso2": "IT", "iso3": "ITA", "m49": 380, "name_uz": "Italiya", "name_en": "Italy", "slug": "italy", "continent": "Europe", "flag_emoji": "🇮🇹", "centroid_lat": 41.8719, "centroid_lon": 12.5674, "bbox": [6.627, 35.493, 18.521, 47.092]},
    {"iso2": "ES", "iso3": "ESP", "m49": 724, "name_uz": "Ispaniya", "name_en": "Spain", "slug": "spain", "continent": "Europe", "flag_emoji": "🇪🇸", "centroid_lat": 40.4637, "centroid_lon": -3.7492, "bbox": [-9.301, 35.947, 4.328, 43.791]},
    {"iso2": "JP", "iso3": "JPN", "m49": 392, "name_uz": "Yaponiya", "name_en": "Japan", "slug": "japan", "continent": "Asia", "flag_emoji": "🇯🇵", "centroid_lat": 36.2048, "centroid_lon": 138.2529, "bbox": [122.934, 24.045, 153.987, 45.523]},
    {"iso2": "KR", "iso3": "KOR", "m49": 410, "name_uz": "Janubiy Koreya", "name_en": "South Korea", "slug": "south-korea", "continent": "Asia", "flag_emoji": "🇰🇷", "centroid_lat": 35.9078, "centroid_lon": 127.7669, "bbox": [124.61, 33.11, 131.87, 38.61]},
    {"iso2": "CN", "iso3": "CHN", "m49": 156, "name_uz": "Xitoy", "name_en": "China", "slug": "china", "continent": "Asia", "flag_emoji": "🇨🇳", "centroid_lat": 35.8617, "centroid_lon": 104.1954, "bbox": [73.499, 18.153, 134.775, 53.561]},
    {"iso2": "IN", "iso3": "IND", "m49": 356, "name_uz": "Hindiston", "name_en": "India", "slug": "india", "continent": "Asia", "flag_emoji": "🇮🇳", "centroid_lat": 20.5937, "centroid_lon": 78.9629, "bbox": [68.163, 6.753, 97.395, 35.504]},
    {"iso2": "BR", "iso3": "BRA", "m49": 76, "name_uz": "Braziliya", "name_en": "Brazil", "slug": "brazil", "continent": "South America", "flag_emoji": "🇧🇷", "centroid_lat": -14.235, "centroid_lon": -51.9253, "bbox": [-73.982, -33.75, -28.847, 5.271]},
    {"iso2": "CA", "iso3": "CAN", "m49": 124, "name_uz": "Kanada", "name_en": "Canada", "slug": "canada", "continent": "North America", "flag_emoji": "🇨🇦", "centroid_lat": 56.1304, "centroid_lon": -106.3468, "bbox": [-141.0, 41.676, -52.648, 83.11]},
    {"iso2": "AU", "iso3": "AUS", "m49": 36, "name_uz": "Avstraliya", "name_en": "Australia", "slug": "australia", "continent": "Oceania", "flag_emoji": "🇦🇺", "centroid_lat": -25.2744, "centroid_lon": 133.7751, "bbox": [112.921, -43.634, 153.637, -10.051]},
    {"iso2": "SA", "iso3": "SAU", "m49": 682, "name_uz": "Saudiya Arabistoni", "name_en": "Saudi Arabia", "slug": "saudi-arabia", "continent": "Asia", "flag_emoji": "🇸🇦", "centroid_lat": 23.8859, "centroid_lon": 45.0792, "bbox": [34.5, 16.37, 55.67, 32.16]},
    {"iso2": "AE", "iso3": "ARE", "m49": 784, "name_uz": "BAA", "name_en": "United Arab Emirates", "slug": "united-arab-emirates", "continent": "Asia", "flag_emoji": "🇦🇪", "centroid_lat": 23.4241, "centroid_lon": 53.8478, "bbox": [51.58, 22.63, 56.38, 26.08]},
    {"iso2": "EG", "iso3": "EGY", "m49": 818, "name_uz": "Misr", "name_en": "Egypt", "slug": "egypt", "continent": "Africa", "flag_emoji": "🇪🇬", "centroid_lat": 26.8206, "centroid_lon": 30.8025, "bbox": [24.7, 22.0, 36.9, 31.67]},
    {"iso2": "UA", "iso3": "UKR", "m49": 804, "name_uz": "Ukraina", "name_en": "Ukraine", "slug": "ukraine", "continent": "Europe", "flag_emoji": "🇺🇦", "centroid_lat": 48.3794, "centroid_lon": 31.1656, "bbox": [22.137, 44.386, 40.228, 52.379]},
    {"iso2": "PL", "iso3": "POL", "m49": 616, "name_uz": "Polsha", "name_en": "Poland", "slug": "poland", "continent": "Europe", "flag_emoji": "🇵🇱", "centroid_lat": 51.9194, "centroid_lon": 19.1451, "bbox": [14.123, 49.002, 24.146, 54.836]},
    {"iso2": "NL", "iso3": "NLD", "m49": 528, "name_uz": "Niderlandiya", "name_en": "Netherlands", "slug": "netherlands", "continent": "Europe", "flag_emoji": "🇳🇱", "centroid_lat": 52.1326, "centroid_lon": 5.2913, "bbox": [3.359, 50.75, 7.228, 53.555]},
    {"iso2": "CH", "iso3": "CHE", "m49": 756, "name_uz": "Shveysariya", "name_en": "Switzerland", "slug": "switzerland", "continent": "Europe", "flag_emoji": "🇨🇭", "centroid_lat": 46.8182, "centroid_lon": 8.2275, "bbox": [5.956, 45.818, 10.492, 47.808]},
    {"iso2": "SE", "iso3": "SWE", "m49": 752, "name_uz": "Shvetsiya", "name_en": "Sweden", "slug": "sweden", "continent": "Europe", "flag_emoji": "🇸🇪", "centroid_lat": 60.1282, "centroid_lon": 18.6435, "bbox": [11.027, 55.337, 24.167, 69.06]},
    {"iso2": "NO", "iso3": "NOR", "m49": 578, "name_uz": "Norvegiya", "name_en": "Norway", "slug": "norway", "continent": "Europe", "flag_emoji": "🇳🇴", "centroid_lat": 60.472, "centroid_lon": 8.4689, "bbox": [4.648, 57.978, 31.057, 71.185]},
    {"iso2": "FI", "iso3": "FIN", "m49": 246, "name_uz": "Finlandiya", "name_en": "Finland", "slug": "finland", "continent": "Europe", "flag_emoji": "🇫🇮", "centroid_lat": 61.9241, "centroid_lon": 25.7482, "bbox": [20.55, 59.8, 31.59, 70.09]},
    {"iso2": "AR", "iso3": "ARG", "m49": 32, "name_uz": "Argentina", "name_en": "Argentina", "slug": "argentina", "continent": "South America", "flag_emoji": "🇦🇷", "centroid_lat": -38.4161, "centroid_lon": -63.6167, "bbox": [-73.577, -55.057, -53.637, -21.781]},
    {"iso2": "MX", "iso3": "MEX", "m49": 484, "name_uz": "Meksika", "name_en": "Mexico", "slug": "mexico", "continent": "North America", "flag_emoji": "🇲🇽", "centroid_lat": 23.6345, "centroid_lon": -102.5528, "bbox": [-118.404, 14.532, -86.71, 32.719]},
    {"iso2": "ID", "iso3": "IDN", "m49": 360, "name_uz": "Indoneziya", "name_en": "Indonesia", "slug": "indonesia", "continent": "Asia", "flag_emoji": "🇮🇩", "centroid_lat": -0.7893, "centroid_lon": 113.9213, "bbox": [95.0, -11.0, 141.0, 6.0]},
    {"iso2": "MY", "iso3": "MYS", "m49": 458, "name_uz": "Malayziya", "name_en": "Malaysia", "slug": "malaysia", "continent": "Asia", "flag_emoji": "🇲🇾", "centroid_lat": 4.2105, "centroid_lon": 101.9758, "bbox": [99.64, 0.85, 119.27, 7.36]},
    {"iso2": "IR", "iso3": "IRN", "m49": 364, "name_uz": "Eron", "name_en": "Iran", "slug": "iran", "continent": "Asia", "flag_emoji": "🇮🇷", "centroid_lat": 32.4279, "centroid_lon": 53.688, "bbox": [44.03, 25.06, 63.32, 39.78]},
    {"iso2": "PK", "iso3": "PAK", "m49": 586, "name_uz": "Pokiston", "name_en": "Pakistan", "slug": "pakistan", "continent": "Asia", "flag_emoji": "🇵🇰", "centroid_lat": 30.3753, "centroid_lon": 69.3451, "bbox": [60.87, 23.63, 77.84, 37.08]},
    {"iso2": "AF", "iso3": "AFG", "m49": 4, "name_uz": "Afg'oniston", "name_en": "Afghanistan", "slug": "afghanistan", "continent": "Asia", "flag_emoji": "🇦🇫", "centroid_lat": 33.9391, "centroid_lon": 67.71, "bbox": [60.52, 29.38, 74.89, 38.49]},
    {"iso2": "GE", "iso3": "GEO", "m49": 268, "name_uz": "Gruziya", "name_en": "Georgia", "slug": "georgia", "continent": "Asia", "flag_emoji": "🇬🇪", "centroid_lat": 42.3154, "centroid_lon": 43.3569, "bbox": [40.0, 41.05, 46.74, 43.59]},
    {"iso2": "AM", "iso3": "ARM", "m49": 51, "name_uz": "Armaniston", "name_en": "Armenia", "slug": "armenia", "continent": "Asia", "flag_emoji": "🇦🇲", "centroid_lat": 40.0691, "centroid_lon": 45.0382, "bbox": [43.45, 38.84, 46.63, 41.3]}
]

async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        for c in COUNTRIES_DATA:
            res = await session.execute(select(Country).where(Country.iso2 == c["iso2"]))
            existing = res.scalar_one_or_none()
            if not existing:
                country = Country(**c)
                session.add(country)
            else:
                for k, v in c.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"Successfully seeded {len(COUNTRIES_DATA)} core countries into database!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
