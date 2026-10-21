# -*- coding: utf-8 -*-
"""
Foldex Admin Kirish Tokenlari (AdminAuthToken) modeli.
Bot orqali /login buyrug'i berilganda generatsiya qilinadigan
bir martalik xavfsiz vaqtincha kirish tokenlarini saqlaydi.
"""

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdminAuthToken(Base):
    """
    Bir martalik kirish tokenlari jadvali.
    Bot ichida /login bosilganda havola orqali brauzerda admin panelga
    avtomatik va xavfsiz kirish imkonini beradi.
    """
    __tablename__ = "admin_auth_tokens"

    # 1. Asosiy identifikator
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # 2. Xavfsiz unikal token qatori
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    # 3. Token berilgan Telegram foydalanuvchi ID (faqat 7883409434 bo'lishi shart)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # 4. Token ishlatilganmi? (Bir martalik xavfsizlik kafolati)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 5. Tokenning amal qilish muddati tugash vaqti (odatda yaratilgandan keyin 15 daqiqa)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # 6. Yaratilgan vaqti
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<AdminAuthToken id={self.id} user_id={self.telegram_user_id} used={self.is_used}>"
