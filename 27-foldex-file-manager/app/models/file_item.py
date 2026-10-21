# -*- coding: utf-8 -*-
"""
Foldex Fayl (FileItem) ma'lumotlar bazasi modeli.
Fayl metama'lumotlari, diskdagi fizik joylashuvi,
hajmi, MIME turi va Telegram `file_id` qiymatlarini saqlaydi.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FileItem(Base):
    """
    Fayllar jadvali modeli.
    Har bir fayl biror papkaga tegishli bo'lishi yoki umumiy bo'lishi mumkin.
    Telegram file_id orqali bot va inline rejimda qayta-qayta yuklamasdan tezkor yuboriladi.
    """
    __tablename__ = "files"

    # 1. Asosiy identifikator
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # 2. Tegishli papka identifikatori (Agar papka o'chirilsa, fayl ham o'chiriladi)
    folder_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # 3. Faylning asl nomi (foydalanuvchi ko'radigan nom, masalan "Darslik_2026.pdf")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # 4. Diskda saqlangan unikal fayl nomi (UUID asosida, masalan "550e8400-e29b-41d4-a716-446655440000.pdf")
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # 5. Faylning uploads katalogiga nisbatan nisbiy yo'li
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # 6. Fayl hajmi (baytlarda, BigInteger - katta hajmli fayllarni qo'llab-quvvatlaydi)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # 7. MIME turi (masalan: "application/pdf", "image/png", "video/mp4")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/octet-stream")

    # 8. Umumlashtirilgan fayl kategoriyasi (document, photo, video, audio, archive, code, other)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, default="document", index=True)

    # 9. Telegram Bot API bilan integratsiya:
    # telegram_file_id: Telegram serverlaridagi kesh identifikatori (inline yuborishda juda tezkor)
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    telegram_file_unique_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 10. Fayl haqida qisqacha izoh/tavsif
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 11. Yaratilgan va yangilangan vaqtlari
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 12. Papka bilan bog'liqlik
    folder: Mapped[Optional["Folder"]] = relationship(
        "Folder",
        back_populates="files"
    )

    def __repr__(self) -> str:
        return f"<FileItem id={self.id} name='{self.name}' size={self.file_size} type='{self.file_type}'>"
