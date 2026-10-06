from __future__ import annotations
import datetime as dt
import secrets
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Integer,
    String, Text, ForeignKey, JSON, UniqueConstraint,
)
from db.base import Base


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)           # Telegram user_id
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    language = Column(String(5), default="uz")
    balance = Column(Integer, default=0)
    referral_code = Column(String(16), unique=True, nullable=False)
    referred_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earned = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    orders_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    otm = Column(String(256), nullable=True)          # oxirgi kiritilgan OTM (titul uchun)
    source = Column(String(32), nullable=True)        # kelish manbai (/start src_xxx)
    marketing_ok = Column(Boolean, default=True)      # marketing xabarlariga rozilik
    created_at = Column(DateTime, default=_now)
    last_active = Column(DateTime, default=_now)

    @staticmethod
    def make_code() -> str:
        return secrets.token_urlsafe(8)[:10]


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    doc_type = Column(String(20), nullable=False)
    topic = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    language = Column(String(5), default="uz")
    page_count = Column(Integer, default=10)
    status = Column(String(20), default="pending")   # pending/generating/done/error/refunded
    price = Column(Integer, default=0)
    paid_from = Column(String(10), default="click")  # balance/click
    ai_provider = Column(String(20), nullable=True)  # claude/openai
    ai_tokens = Column(Integer, default=0)
    file_path = Column(String(255), nullable=True)
    file_format = Column(String(10), nullable=True)
    tg_file_id = Column(String(256), nullable=True)
    error_msg = Column(Text, nullable=True)
    source_text = Column(Text, nullable=True)         # yakuniy markdown (revizyon uchun)
    revisions = Column(Integer, default=0)            # ishlatilgan revizyonlar soni
    created_at = Column(DateTime, default=_now)
    completed_at = Column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    click_trans_id = Column(String(64), nullable=True)
    merchant_trans_id = Column(String(64), unique=True, nullable=True)
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")   # pending/paid/cancelled/error
    payment_type = Column(String(20), default="click")
    created_at = Column(DateTime, default=_now)
    paid_at = Column(DateTime, nullable=True)


class Setting(Base):
    """Admin paneldan sozlanadigan kalit/qiymat (narx, bonus, rejim)."""
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_now)


class Rating(Base):
    """Buyurtma bahosi (⭐ 1-5) va izoh."""
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    stars = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    referee_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    bonus_awarded = Column(Boolean, default=False)
    bonus_amount = Column(Integer, default=0)
    bonus_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    __table_args__ = (UniqueConstraint("referrer_id", "referee_id"),)
