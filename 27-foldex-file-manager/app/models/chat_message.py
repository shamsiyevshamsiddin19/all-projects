# -*- coding: utf-8 -*-
"""
Foldex Bot Chat Xabarlari Modeli.
Chatdagi xabarlar ID sini kuzatib boradi va har kechqurun avtomatik
tozalashda faqat /start xabarlarini saqlab, boshqa barcha xabarlarni
o'chirish imkonini beradi.
"""

from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BotChatMessage(Base):
    """Telegram chatdagi xabarlar identifikatorlarini saqlovchi jadval."""
    __tablename__ = "bot_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    is_start: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
