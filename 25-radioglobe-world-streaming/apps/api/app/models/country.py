from sqlalchemy import (
    Column, DateTime, Float, Index, Integer, SmallInteger, String, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    # ISO 3166-1 alpha-2 — ichki kalit va URL uchun.
    # Nizoli hududlar uchun "CY-N" kabi 4 belgili kod ham bo'lishi mumkin.
    iso2 = Column(String(5), primary_key=True)
    iso3 = Column(String(3), nullable=False)
    # M49 — XARITA KALITI. GeoJSON bilan aynan shu orqali bog'lanadi, chunki
    # Natural Earth ma'lumotida ISO_A2 ba'zi davlatlarda "-99" bo'lib chiqadi.
    m49 = Column(SmallInteger, nullable=False, unique=True, index=True)

    name_en = Column(String, nullable=False)
    name_uz = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    continent = Column(String, nullable=False)
    flag_emoji = Column(String(16), nullable=True)

    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    bbox = Column(JSONB, nullable=True)  # [min_lon, min_lat, max_lon, max_lat]

    radio_count = Column(Integer, nullable=False, default=0)
    tv_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel_links = relationship(
        "ChannelCountry", back_populates="country", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_countries_radio_count", "radio_count"),
    )
