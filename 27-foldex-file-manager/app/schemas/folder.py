# -*- coding: utf-8 -*-
"""
Foldex Papka Pydantic sxemalari.
API orqali papkalarni yaratish, tahrirlash, daraxt ko'rinishida
olish va breadcrumb navigatsiyasini taqdim etish uchun xizmat qiladi.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BreadcrumbItem(BaseModel):
    """Navigatsiya zanjiridagi (breadcrumb) har bir papka qadami."""
    id: Optional[int] = Field(None, description="Papka ID si (None bo'lsa ildiz)")
    name: str = Field(..., description="Papka nomi")
    icon: str = Field("📁", description="Papka ikonkasi")


class FolderBase(BaseModel):
    """Papkaning asosiy maydonlari."""
    name: str = Field(..., min_length=1, max_length=255, description="Papka nomi")
    parent_id: Optional[int] = Field(None, description="Ota papka ID si (NULL bo'lsa ildiz papka)")
    icon: str = Field("📁", max_length=64, description="Emoji yoki ikonka")
    color: str = Field("indigo", max_length=32, description="Papka vizual rangi")
    description: Optional[str] = Field(None, description="Papka haqida qisqacha tavsif")
    order_index: int = Field(0, description="Tartib indeksi")


class FolderCreate(FolderBase):
    """Yangi papka yaratish uchun so'rov sxemasi."""
    pass


class FolderUpdate(BaseModel):
    """Mavjud papkani tahrirlash yoki boshqa joyga ko'chirish sxemasi."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[int] = Field(None, description="Yangi ota papka ID si (ko'chirish uchun)")
    icon: Optional[str] = Field(None, max_length=64)
    color: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None)
    order_index: Optional[int] = Field(None)


class FolderOut(FolderBase):
    """Foydalanuvchiga qaytariladigan to'liq papka ma'lumotlari."""
    id: int
    created_at: datetime
    updated_at: datetime
    subfolders_count: int = Field(0, description="Ichki papkalar soni")
    files_count: int = Field(0, description="Ichidagi fayllar soni")
    total_size_bytes: int = Field(0, description="Fayllarning umumiy hajmi baytlarda")

    model_config = ConfigDict(from_attributes=True)


class FolderTreeNode(BaseModel):
    """Daraxt (tree) ko'rinishidagi papkalar ierarxiyasi."""
    id: int
    name: str
    icon: str = "📁"
    color: str = "indigo"
    parent_id: Optional[int] = None
    children: List["FolderTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)


class FolderDetailResponse(BaseModel):
    """Joriy papka va uning to'liq tarkibi (ichki papkalar, fayllar va breadcrumb)."""
    folder: Optional[FolderOut] = None
    breadcrumbs: List[BreadcrumbItem] = []
    subfolders: List[FolderOut] = []
    total_files: int = 0
    total_subfolders: int = 0
