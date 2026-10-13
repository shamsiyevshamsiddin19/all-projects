from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CountryBase(BaseModel):
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
    centroid: Optional[List[float]] = None
    bbox: Optional[List[float]] = None
    top_tags: List[str] = []
    languages: List[str] = []

    class Config:
        from_attributes = True

class CountryCountsResponse(BaseModel):
    counts: Dict[str, Dict[str, int]] # {"UZ": {"radio": 42, "tv": 0}}
