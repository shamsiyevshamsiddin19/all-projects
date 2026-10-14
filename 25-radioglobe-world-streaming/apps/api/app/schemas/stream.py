from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StreamInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    format: Optional[str] = "mp3"
    bitrate: Optional[int] = None
    is_https: bool = False
    needs_proxy: bool = True
    score: int = 0
    play_url: Optional[str] = None


class PlayRequest(BaseModel):
    stream_id: int = Field(..., gt=0)


class PlayResponse(BaseModel):
    stream_id: int
    station_name: str
    play_url: str
    is_proxied: bool
    format: Optional[str] = "mp3"
