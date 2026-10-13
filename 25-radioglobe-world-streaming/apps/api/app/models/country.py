from sqlalchemy import Column, String, SmallInteger, Integer, Float, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Country(Base):
    __tablename__ = "countries"

    iso2 = Column(String(2), primary_key=True, index=True)         # 'UZ'
    iso3 = Column(String(3), nullable=False)                      # 'UZB'
    m49 = Column(SmallInteger, nullable=False, unique=True, index=True) # 860 - XARITA KALITI
    name_en = Column(String, nullable=False)                      # 'Uzbekistan'
    name_uz = Column(String, nullable=False)                      # 'O\'zbekiston'
    name_native = Column(String, nullable=True)
    slug = Column(String, nullable=False, unique=True, index=True) # 'uzbekistan'
    continent = Column(String, nullable=False)                    # 'Asia'
    flag_emoji = Column(String, nullable=True)                    # '🇺🇿'
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    bbox = Column(JSON, nullable=True)                            # [min_lon, min_lat, max_lon, max_lat]
    radio_count = Column(Integer, nullable=False, default=0)
    tv_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel_links = relationship("ChannelCountry", back_populates="country", cascade="all, delete-orphan")
