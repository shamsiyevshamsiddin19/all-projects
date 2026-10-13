from sqlalchemy import Column, BigInteger, String, Boolean, Integer, SmallInteger, JSON, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    type = Column(String(10), nullable=False, default="radio") # 'radio' | 'tv'
    name = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)
    logo_url = Column(String, nullable=True)
    homepage = Column(String, nullable=True)
    languages = Column(JSON, nullable=False, default=list)      # ['uz', 'ru']
    tags = Column(JSON, nullable=False, default=list)           # ['pop', 'news', 'talk']
    bitrate_max = Column(SmallInteger, nullable=True)
    source = Column(String, nullable=False, default="radio-browser") # 'radio-browser' | 'iptv-org' | 'manual'
    external_ids = Column(JSON, nullable=False, default=dict)   # {"radiobrowser_uuid": "..."}
    is_archived = Column(Boolean, nullable=False, default=False)
    popularity = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("type", "slug", name="uq_channel_type_slug"),
    )

    streams = relationship("Stream", back_populates="channel", cascade="all, delete-orphan")
    country_links = relationship("ChannelCountry", back_populates="channel", cascade="all, delete-orphan")


class ChannelCountry(Base):
    __tablename__ = "channel_countries"

    channel_id = Column(BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    country_iso2 = Column(String(2), ForeignKey("countries.iso2", ondelete="CASCADE"), primary_key=True, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    channel = relationship("Channel", back_populates="country_links")
    country = relationship("Country", back_populates="channel_links")
