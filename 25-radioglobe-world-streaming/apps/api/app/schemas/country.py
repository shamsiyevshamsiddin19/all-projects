from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CountryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    iso2: str
    iso3: str
    m49: int
    name_uz: str
    name_en: str
    slug: str
    continent: str
    flag_emoji: Optional[str] = None
    radio_count: int = 0
    tv_count: int = 0


class CountrySimple(CountryBase):
    pass


class CountryDetail(CountryBase):
    centroid: Optional[List[float]] = None   # [lat, lon]
    bbox: Optional[List[float]] = None       # [min_lon, min_lat, max_lon, max_lat]
    top_tags: List[str] = []
    languages: List[str] = []


class CountryCountsResponse(BaseModel):
    counts: Dict[str, Dict[str, int]]
