# -*- coding: utf-8 -*-
"""
Foldex Statistika API yo'llari (Stats API).
Diskdan foydalanish, papkalar va fayllar soni, fayl toifalari
bo'yicha ko'rsatkichlarni boshqaruv paneliga taqdim etadi.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.file_item import FileItem
from app.models.folder import Folder
from app.schemas.file_item import format_bytes
from app.services.file_service import FileService

router = APIRouter(prefix="/api/stats", tags=["Statistika"])


@router.get("/dashboard")
async def get_dashboard_stats(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Admin panelning asosiy metrikalari va statistika bloklari."""
    # 1. Umumiy papkalar soni
    total_folders = (await db.execute(select(func.count(Folder.id)))).scalar() or 0

    # 2. Umumiy fayllar soni va umumiy xotira hajmi
    file_res = (
        await db.execute(
            select(
                func.count(FileItem.id),
                func.coalesce(func.sum(FileItem.file_size), 0)
            )
        )
    ).first()

    total_files = file_res[0] if file_res else 0
    total_size_bytes = int(file_res[1]) if file_res else 0

    # 3. Fayl turlari bo'yicha guruhlash
    type_stmt = (
        select(FileItem.file_type, func.count(FileItem.id))
        .group_by(FileItem.file_type)
    )
    type_rows = (await db.execute(type_stmt)).all()
    categories = {row[0]: row[1] for row in type_rows}

    # 4. Eng so'nggi yuklangan 5 ta fayl
    recent_stmt = (
        select(FileItem)
        .order_by(FileItem.created_at.desc())
        .limit(5)
    )
    recent_res = (await db.execute(recent_stmt)).scalars().all()
    recent_files = [FileService.to_schema(f) for f in recent_res]

    max_bytes = settings.max_upload_size_bytes
    used_percentage = round((total_size_bytes / max_bytes) * 100, 2) if max_bytes > 0 else 0

    return {
        "total_folders": total_folders,
        "total_files": total_files,
        "total_size_bytes": total_size_bytes,
        "total_size_formatted": format_bytes(total_size_bytes),
        "storage_limit_formatted": f"{settings.MAX_UPLOAD_SIZE_MB} MB",
        "storage_used_percent": min(used_percentage, 100.0),
        "categories": {
            "document": categories.get("document", 0),
            "photo": categories.get("photo", 0),
            "video": categories.get("video", 0),
            "audio": categories.get("audio", 0),
            "archive": categories.get("archive", 0),
            "code": categories.get("code", 0),
            "other": categories.get("other", 0),
        },
        "recent_files": recent_files
    }
