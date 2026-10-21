# -*- coding: utf-8 -*-
"""
Foldex Fayl Pydantic sxemalari.
Fayllarni yuklash, ko'rish, nomini o'zgartirish, ko'chirish
va qulay formatlangan hajmni ko'rsatish uchun xizmat qiladi.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


def format_bytes(size: int) -> str:
    """Baytlarni o'qilishi oson formatga (B, KB, MB, GB) o'tkazuvchi yordamchi funksiya."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


class FileItemBase(BaseModel):
    """Faylning asosiy maydonlari."""
    name: str = Field(..., min_length=1, max_length=255, description="Fayl nomi")
    folder_id: Optional[int] = Field(None, description="Tegishli papka identifikatori")
    description: Optional[str] = Field(None, description="Qisqacha izoh")


class FileItemUpdate(BaseModel):
    """Fayl nomini yoki papkasini o'zgartirish sxemasi."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    folder_id: Optional[int] = Field(None, description="Ko'chiriladigan yangi papka ID")
    description: Optional[str] = Field(None)


class FileItemOut(FileItemBase):
    """Mijozga qaytariladigan to'liq fayl ma'lumotlari."""
    id: int
    file_size: int
    mime_type: str
    file_type: str
    telegram_file_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    download_url: Optional[str] = None
    formatted_size: Optional[str] = None
    is_synced_with_telegram: bool = False

    model_config = ConfigDict(from_attributes=True)


class FileListResponse(BaseModel):
    """Fayllar ro'yxati va umumiy statistika."""
    total: int
    items: list[FileItemOut]
