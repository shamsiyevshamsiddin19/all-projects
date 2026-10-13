from pydantic import BaseModel
from typing import Optional, List

class StreamInfo(BaseModel):
    id: int
    format: Optional[str] = "mp3"
    bitrate: Optional[int] = 128
    is_https: bool = False
    needs_proxy: bool = True
    score: int = 100
    play_url: Optional[str] = None # Stream proxy or direct URL

    class Config:
        from_attributes = True

class PlayRequest(BaseModel):
    stream_id: int

class PlayResponse(BaseModel):
    stream_id: int
    station_name: str
    play_url: str
    is_proxied: bool
    format: Optional[str] = "mp3"
