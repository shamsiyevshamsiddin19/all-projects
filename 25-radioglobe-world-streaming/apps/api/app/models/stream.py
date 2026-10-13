from sqlalchemy import Column, BigInteger, String, Boolean, SmallInteger, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

class Stream(Base):
    __tablename__ = "streams"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    channel_id = Column(BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    url_resolved = Column(String, nullable=True)
    format = Column(String(20), nullable=True)                # 'mp3' | 'aac' | 'hls'
    bitrate = Column(SmallInteger, nullable=True)             # kbps
    is_https = Column(Boolean, nullable=False, default=False)
    sends_cors = Column(Boolean, nullable=False, default=False)
    is_geo_blocked = Column(Boolean, nullable=False, default=False)
    needs_proxy = Column(Boolean, nullable=False, default=True)
    last_ok_at = Column(DateTime(timezone=True), nullable=True)
    fail_count = Column(SmallInteger, nullable=False, default=0)
    score = Column(SmallInteger, nullable=False, default=100, index=True) # 0-100
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel = relationship("Channel", back_populates="streams")
    checks = relationship("StreamCheck", back_populates="stream", cascade="all, delete-orphan")


class StreamCheck(Base):
    __tablename__ = "stream_checks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stream_id = Column(BigInteger, ForeignKey("streams.id", ondelete="CASCADE"), nullable=False, index=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status_code = Column(SmallInteger, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    headers_seen = Column(JSON, nullable=False, default=dict)

    stream = relationship("Stream", back_populates="checks")
