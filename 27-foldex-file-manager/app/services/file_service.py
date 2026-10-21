# -*- coding: utf-8 -*-
"""
Foldex Fayllar bilan ishlash xizmati (File Service).
Diskdagi xotira tizimi, asinxron fayl yuklash, o'qish,
nomini o'zgartirish, ko'chirish va xavfsiz o'chirish amallarini bajaradi.
"""

import mimetypes
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import aiofiles
from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import sanitize_filename
from app.models.file_item import FileItem
from app.models.folder import Folder
from app.schemas.file_item import FileItemOut, FileItemUpdate, format_bytes


# Fayl kengaytmasi bo'yicha umumiy kategoriyani aniqlash lug'ati
FILE_TYPE_MAPPING = {
    # Rasmlar
    ".png": "photo", ".jpg": "photo", ".jpeg": "photo", ".webp": "photo",
    ".gif": "photo", ".svg": "photo", ".bmp": "photo",
    # Videolar
    ".mp4": "video", ".mkv": "video", ".avi": "video", ".mov": "video",
    ".webm": "video", ".flv": "video",
    # Audiolar
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio",
    ".flac": "audio", ".aac": "audio",
    # Arxivlar
    ".zip": "archive", ".rar": "archive", ".7z": "archive", ".tar": "archive",
    ".gz": "archive",
    # Kod fayllari
    ".py": "code", ".js": "code", ".ts": "code", ".html": "code",
    ".css": "code", ".json": "code", ".sql": "code", ".sh": "code",
    ".cpp": "code", ".java": "code",
    # Hujjatlar
    ".pdf": "document", ".doc": "document", ".docx": "document",
    ".xls": "document", ".xlsx": "document", ".ppt": "document",
    ".pptx": "document", ".txt": "document"
}


class FileService:
    """Fayllar ustida barcha operatsiyalarni bajaruvchi asinxron xizmat klassi."""

    @staticmethod
    def detect_file_type(filename: str, mime_type: str) -> str:
        """Fayl kengaytmasi va MIME turiga qarab umumiy kategoriyani aniqlaydi."""
        ext = Path(filename).suffix.lower()
        if ext in FILE_TYPE_MAPPING:
            return FILE_TYPE_MAPPING[ext]

        if mime_type.startswith("image/"):
            return "photo"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif "pdf" in mime_type or "word" in mime_type or "sheet" in mime_type or "document" in mime_type:
            return "document"
        elif "zip" in mime_type or "compressed" in mime_type or "tar" in mime_type:
            return "archive"

        return "document"

    @staticmethod
    async def get_by_id(db: AsyncSession, file_id: int) -> Optional[FileItem]:
        """Faylni ID bo'yicha qidiradi."""
        stmt = select(FileItem).where(FileItem.id == file_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_files_by_folder(
        db: AsyncSession,
        folder_id: Optional[int],
        search: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> List[FileItem]:
        """Berilgan papkadagi fayllarni filtrlab qaytaradi."""
        stmt = select(FileItem)

        if folder_id is None:
            # Asosiy ildizdagi (papkasi belgilanmagan) fayllar
            stmt = stmt.where(FileItem.folder_id.is_(None))
        else:
            stmt = stmt.where(FileItem.folder_id == folder_id)

        if search and search.strip():
            stmt = stmt.where(FileItem.name.ilike(f"%{search.strip()}%"))

        if file_type and file_type != "all":
            stmt = stmt.where(FileItem.file_type == file_type)

        stmt = stmt.order_by(FileItem.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def search_all_files(db: AsyncSession, query: str) -> List[FileItem]:
        """Barcha papkalar bo'yicha global qidiruv."""
        stmt = (
            select(FileItem)
            .where(
                or_(
                    FileItem.name.ilike(f"%{query.strip()}%"),
                    FileItem.description.ilike(f"%{query.strip()}%")
                )
            )
            .order_by(FileItem.created_at.desc())
            .limit(50)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def save_upload(
        db: AsyncSession,
        file: UploadFile,
        folder_id: Optional[int] = None,
        description: Optional[str] = None,
        telegram_file_id: Optional[str] = None
    ) -> FileItem:
        """
        Yuklangan faylni xavfsiz holda diskka yozadi va ma'lumotlar bazasiga saqlaydi.
        Katta hajmdagi fayllar xotirada qotib qolmasligi uchun bo'laklab (chunked) yoziladi.
        """
        # 1. Asl fayl nomini tozalash (Xavfsizlik: Path traversal oldini olish)
        original_name = sanitize_filename(file.filename or "nomsiz_fayl")
        ext = Path(original_name).suffix.lower()

        # 2. Diskda saqlash uchun unikal UUID nom yaratish
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        storage_dir = Path(settings.STORAGE_DIR)
        storage_dir.mkdir(parents=True, exist_ok=True)
        disk_path = storage_dir / stored_filename

        # 3. Faylni diskka yozish va umumiy hajmni hisoblash
        total_size = 0
        chunk_size = 1024 * 1024  # 1 MB li bo'laklar bilan yozish
        max_bytes = settings.max_upload_size_bytes

        async with aiofiles.open(disk_path, "wb") as out_file:
            while content := await file.read(chunk_size):
                total_size += len(content)
                if total_size > max_bytes:
                    # Fayl hajmi limitdan oshib ketsa, yozilgan qismini o'chiramiz
                    await file.close()
                    if disk_path.exists():
                        disk_path.unlink()
                    raise ValueError(f"Fayl hajmi ruxsat etilgan limitdan ({settings.MAX_UPLOAD_SIZE_MB} MB) oshib ketdi!")
                await out_file.write(content)

        # 4. MIME va umumiy fayl turini aniqlash
        mime_type = file.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        file_type = FileService.detect_file_type(original_name, mime_type)

        # 5. Bazaga yangi yozuv qo'shish
        file_item = FileItem(
            name=original_name,
            folder_id=folder_id,
            stored_filename=stored_filename,
            file_path=stored_filename,  # uploads papkasiga nisbatan nisbiy yo'l
            file_size=total_size,
            mime_type=mime_type,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            description=description
        )

        db.add(file_item)
        await db.commit()
        await db.refresh(file_item)
        return file_item

    @staticmethod
    async def update_file(
        db: AsyncSession,
        file_id: int,
        file_in: FileItemUpdate
    ) -> Optional[FileItem]:
        """Fayl nomini, papkasini yoki tavsifini o'zgartiradi."""
        file_item = await FileService.get_by_id(db, file_id)
        if not file_item:
            return None

        update_data = file_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"]:
            # Yangi nom berilganda, asl kengaytmasini saqlab qolish yoki tozalash
            new_name = sanitize_filename(update_data["name"])
            file_item.name = new_name
            # Yangi kengaytma bo'yicha fayl turini yangilash
            file_item.file_type = FileService.detect_file_type(new_name, file_item.mime_type)

        if "folder_id" in update_data:
            target_folder_id = update_data["folder_id"]
            if target_folder_id is not None:
                folder = await db.execute(select(Folder).where(Folder.id == target_folder_id))
                if not folder.scalar_one_or_none():
                    raise ValueError("Ko'rsatilgan maqsadli papka mavjud emas!")
            file_item.folder_id = target_folder_id

        if "description" in update_data:
            file_item.description = update_data["description"]

        await db.commit()
        await db.refresh(file_item)
        return file_item

    @staticmethod
    async def delete_file(db: AsyncSession, file_id: int) -> bool:
        """Faylni bazadan va diskdan butunlay o'chiradi."""
        file_item = await FileService.get_by_id(db, file_id)
        if not file_item:
            return False

        # Diskdagi fizik faylni o'chirish
        disk_path = Path(settings.STORAGE_DIR) / file_item.file_path
        if disk_path.exists():
            try:
                disk_path.unlink()
            except Exception as e:
                pass  # Fayl o'chirishda xatolik bo'lsa ham DB yozuvi o'chirilishi kerak

        # Bazadan o'chirish
        await db.delete(file_item)
        await db.commit()
        return True

    @staticmethod
    def to_schema(file_item: FileItem) -> FileItemOut:
        """FileItem modelini frontend uchun tayyor FileItemOut sxemasiga aylantiradi."""
        return FileItemOut(
            id=file_item.id,
            folder_id=file_item.folder_id,
            name=file_item.name,
            file_size=file_item.file_size,
            mime_type=file_item.mime_type,
            file_type=file_item.file_type,
            telegram_file_id=file_item.telegram_file_id,
            description=file_item.description,
            created_at=file_item.created_at,
            updated_at=file_item.updated_at,
            download_url=f"/api/files/{file_item.id}/download",
            formatted_size=format_bytes(file_item.file_size),
            is_synced_with_telegram=bool(file_item.telegram_file_id)
        )
