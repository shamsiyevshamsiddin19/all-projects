from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer,
    SmallInteger, String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Stream(Base):
    __tablename__ = "streams"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_id = Column(
        BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url = Column(String, nullable=False)
    url_resolved = Column(String, nullable=True)
    format = Column(String(20), nullable=True)
    bitrate = Column(SmallInteger, nullable=True)

    # Kichik raqam = avval sinab ko'riladi (zaxira oqimlar tartibi)
    priority = Column(SmallInteger, nullable=False, default=0)

    # Health checker aniqlaydigan imkoniyatlar
    is_https = Column(Boolean, nullable=False, default=False)
    sends_cors = Column(Boolean, nullable=False, default=False)
    is_geo_blocked = Column(Boolean, nullable=False, default=False)
    needs_proxy = Column(Boolean, nullable=False, default=True)

    # Health checker aniqlaydigan holat
    last_ok_at = Column(DateTime(timezone=True), nullable=True)
    # Oldin bu ustun yo'q edi va navbat `last_ok_at` bo'yicha tuzilardi —
    # natijada hech qachon ishlamagan oqim (last_ok_at = NULL) har safar
    # birinchi bo'lib tekshirilaverib, katalogning qolgani navbatga yetmasdi.
    last_check_at = Column(DateTime(timezone=True), nullable=True)
    # Keyingi tekshiruv vaqti — exponential backoff shu ustun orqali ishlaydi
    next_check_at = Column(DateTime(timezone=True), nullable=True)
    fail_count = Column(SmallInteger, nullable=False, default=0)
    score = Column(SmallInteger, nullable=False, default=50)
    latency_ms = Column(Integer, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel = relationship("Channel", back_populates="streams")
    checks = relationship("StreamCheck", back_populates="stream", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("channel_id", "url", name="uq_stream_channel_url"),
        # Frontend uchun asosiy so'rov: kanalning eng yaxshi ishlaydigan oqimi
        Index(
            "ix_streams_playable",
            "channel_id", "priority", "score",
            postgresql_where=Column("is_active") == True,  # noqa: E712
        ),
        # Health checker navbati
        Index("ix_streams_check_queue", "next_check_at"),
    )


class StreamCheck(Base):
    """Oqim tekshiruvlari tarixi.

    Bu jadval tez o'sadi (50k oqim x kuniga ~10 tekshiruv = oyiga ~15 mln qator),
    shuning uchun `checked_at` bo'yicha oylik partition qilinadi. Partition
    yaratish va eskisini o'chirish Alembic migratsiyasida va worker'ning
    tozalash vazifasida bajariladi.
    """

    __tablename__ = "stream_checks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Partition kaliti PK ning bir qismi bo'lishi SHART
    checked_at = Column(
        DateTime(timezone=True), primary_key=True, server_default=func.now(), index=True
    )
    stream_id = Column(
        BigInteger, ForeignKey("streams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ok = Column(Boolean, nullable=False, default=False)
    status_code = Column(SmallInteger, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error = Column(String(300), nullable=True)
    headers_seen = Column(JSONB, nullable=False, default=dict)

    stream = relationship("Stream", back_populates="checks")
