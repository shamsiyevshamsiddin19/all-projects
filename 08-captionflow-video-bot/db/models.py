"""SQLAlchemy modellari (arxitektura 7-bo'lim, MVP qismi).

Vaqtlar — naive UTC (SQLite uchun soddaroq).
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="uz")
    plan: Mapped[str] = mapped_column(String(16), default="free")
    plan_until: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    last_active_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    # Referal: kim taklif qilgan (User.id) va referaldan olingan bonus.
    # bonus_videos oylik bepul limitga DOIMIY qo'shiladi (har taklif +N video/oy).
    referred_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    bonus_videos: Mapped[int] = mapped_column(Integer, default=0)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan: Mapped[str] = mapped_column(String(16))
    amount: Mapped[int] = mapped_column(Integer)  # so'm
    status: Mapped[str] = mapped_column(String(16), default="pending")
    provider: Mapped[str] = mapped_column(String(16), default="click")
    click_trans_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    paid_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    # Uzun video (45+ daqiqa) bir martalik to'lovi uchun: video havolasi/file_id,
    # rejim, til va h.k. JSON holida — to'lov tasdiqlangach (webhook) shu
    # ma'lumot bilan video avtomatik navbatga qo'yiladi (plan="longvideo").
    meta: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)  # so'm
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    click_trans_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    paid_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), default="")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="upload")
    mode: Mapped[str] = mapped_column(String(64), default="original")
    target_lang: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    error_step: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    translation_provider: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
