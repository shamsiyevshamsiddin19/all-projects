from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.stream import StreamInfo


class ChannelSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    slug: str
    name: str
    logo_url: Optional[str] = None
    tags: List[str] = []
    languages: List[str] = []
    bitrate: Optional[int] = None
    score: int = 0
    primary_stream: Optional[StreamInfo] = None
    # Birinchi oqim ishlamasa frontend shu ro'yxat bo'yicha navbatma-navbat
    # urinib ko'radi (hujjatdagi "zaxira oqimga avtomatik o'tish" talabi)
    fallback_streams: List[StreamInfo] = []


class ChannelDetail(ChannelSimple):
    homepage: Optional[str] = None
    popularity: int = 0
    streams: List[StreamInfo] = []
    country_iso2: Optional[str] = None


class ChannelListResponse(BaseModel):
    # Bazadagi umumiy son (sahifadagi elementlar soni emas)
    total: int
    items: List[ChannelSimple]
    # Keyset kursori — opaque satr
    next_cursor: Optional[str] = None
