from pydantic import BaseModel
from typing import Optional, List
from app.schemas.stream import StreamInfo

class ChannelSimple(BaseModel):
    id: int
    type: str # 'radio' | 'tv'
    slug: str
    name: str
    logo_url: Optional[str] = None
    tags: List[str] = []
    languages: List[str] = []
    bitrate: Optional[int] = 128
    score: int = 100
    primary_stream: Optional[StreamInfo] = None

    class Config:
        from_attributes = True

class ChannelDetail(ChannelSimple):
    homepage: Optional[str] = None
    popularity: int = 0
    streams: List[StreamInfo] = []

class ChannelListResponse(BaseModel):
    total: int
    items: List[ChannelSimple]
    next_cursor: Optional[int] = None
