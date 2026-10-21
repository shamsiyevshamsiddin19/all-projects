# -*- coding: utf-8 -*-
"""
Foldex Papka (Folder) ma'lumotlar bazasi modeli.
Ierarxik papkalar tuzilmasi (cheksiz ichma-ich papkalar daraxti)
va kaskadli o'chirish qoidalarini ta'minlaydi.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Folder(Base):
    """
    Papkalar jadvali modeli.
    Cheksiz chuqurlikdagi ierarxiyani (parent-child relationship) o'zida saqlaydi.
    """
    __tablename__ = "folders"

    # 1. Asosiy identifikator
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # 2. Papka nomi (masalan: "Rus tili", "Grammatika", "Padejlar")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # 3. Ota papka identifikatori (Agar NULL bo'lsa, bu asosiy/ildiz papka hisoblanadi)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # 4. Papka vizual ko'rinishi (Emoji ikonkasi va rangi)
    icon: Mapped[str] = mapped_column(String(64), default="📁", nullable=False)
    color: Mapped[str] = mapped_column(String(32), default="indigo", nullable=False)

    # 5. Qisqacha tavsif
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 6. Saralash indeksi (Tartib raqami)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 7. Vaqt belgilari
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

    # 8. O'z-o'ziga bog'lanish (Self-referential parent-children relationship)
    # Ota papka o'chirilganda, barcha bolalari ham kaskadli ravishda avtomatik o'chiriladi
    parent: Mapped[Optional["Folder"]] = relationship(
        "Folder",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["Folder"]] = relationship(
        "Folder",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Folder.order_index, Folder.name"
    )

    # 9. Ushbu papkaga tegishli fayllar bilan bog'lanish
    files: Mapped[List["FileItem"]] = relationship(
        "FileItem",
        back_populates="folder",
        cascade="all, delete-orphan",
        order_by="FileItem.name"
    )

    def __repr__(self) -> str:
        return f"<Folder id={self.id} name='{self.name}' parent_id={self.parent_id}>"
