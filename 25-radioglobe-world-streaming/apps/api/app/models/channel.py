from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer,
    SmallInteger, String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(String(10), nullable=False, default="radio")
    name = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)
    logo_url = Column(String, nullable=True)
    homepage = Column(String, nullable=True)

    # JSON emas, JSONB: JSON ustunida GIN indeks va `@>` operatori ishlamaydi,
    # shuning uchun tag/til bo'yicha filtr sekin va ishonchsiz edi.
    languages = Column(JSONB, nullable=False, default=list)
    tags = Column(JSONB, nullable=False, default=list)
    external_ids = Column(JSONB, nullable=False, default=dict)

    bitrate_max = Column(SmallInteger, nullable=True)
    source = Column(String, nullable=False, default="radio-browser")
    is_archived = Column(Boolean, nullable=False, default=False, index=True)
    popularity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("type", "slug", name="uq_channel_type_slug"),
        Index(
            "ix_channels_type_popularity",
            "type", "popularity",
            postgresql_where=Column("is_archived") == False,  # noqa: E712
        ),
        Index("ix_channels_tags_gin", "tags", postgresql_using="gin"),
        Index("ix_channels_languages_gin", "languages", postgresql_using="gin"),
        Index("ix_channels_external_gin", "external_ids", postgresql_using="gin"),
    )

    streams = relationship("Stream", back_populates="channel", cascade="all, delete-orphan")
    country_links = relationship(
        "ChannelCountry", back_populates="channel", cascade="all, delete-orphan"
    )


class ChannelCountry(Base):
    __tablename__ = "channel_countries"

    channel_id = Column(
        BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True
    )
    country_iso2 = Column(
        String(2), ForeignKey("countries.iso2", ondelete="CASCADE"),
        primary_key=True, index=True,
    )
    is_primary = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        # Har kanalda ko'pi bilan bitta asosiy davlat bo'lishini baza kafolatlaydi
        Index(
            "uq_channel_single_primary",
            "channel_id",
            unique=True,
            postgresql_where=Column("is_primary") == True,  # noqa: E712
        ),
    )

    channel = relationship("Channel", back_populates="country_links")
    country = relationship("Country", back_populates="channel_links")
