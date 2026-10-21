# -*- coding: utf-8 -*-
"""
Foldex Papkalar API yo'llari (Folders API).
Papkalar ierarxiyasini yaratish, ko'rish, daraxt (tree) ko'rinishida olish,
tahrirlash, boshqa papkaga ko'chirish va o'chirish amallarini boshqaradi.
Barcha endpointlar faqat TELEGRAM_ADMIN_ID (7883409434) uchun himoyalangan.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.schemas.folder import (
    BreadcrumbItem,
    FolderCreate,
    FolderDetailResponse,
    FolderOut,
    FolderTreeNode,
    FolderUpdate
)
from app.services.folder_service import FolderService

router = APIRouter(prefix="/api/folders", tags=["Papkalar"])


@router.get("/", response_model=List[FolderOut])
async def list_folders(
    parent_id: Optional[int] = Query(None, description="Ota papka ID si (None bo'lsa ildiz papkalar)"),
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Papkalar ro'yxatini ichki statistikalari (fayllar va papkalar soni) bilan qaytaradi."""
    folders = await FolderService.get_subfolders(db, parent_id)
    return [await FolderService.get_folder_with_stats(db, f) for f in folders]


@router.get("/tree", response_model=List[FolderTreeNode])
async def get_folder_tree(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Sidebar uchun to'liq ierarxik papkalar daraxtini qaytaradi."""
    return await FolderService.get_folder_tree(db)


@router.get("/{folder_id}", response_model=FolderDetailResponse)
async def get_folder_detail(
    folder_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Muayyan papka tafsilotlarini, uning breadcrumb yo'lini va
    bevosita ichki papkalarini qaytaradi.
    """
    folder = await FolderService.get_by_id(db, folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Papka topilmadi!"
        )

    folder_out = await FolderService.get_folder_with_stats(db, folder)
    breadcrumbs = await FolderService.get_breadcrumbs(db, folder_id)
    subfolders = await FolderService.get_subfolders(db, folder_id)
    subfolders_out = [await FolderService.get_folder_with_stats(db, sf) for sf in subfolders]

    return FolderDetailResponse(
        folder=folder_out,
        breadcrumbs=breadcrumbs,
        subfolders=subfolders_out,
        total_files=folder_out.files_count,
        total_subfolders=len(subfolders)
    )


@router.get("/breadcrumbs/root", response_model=List[BreadcrumbItem])
async def get_root_breadcrumbs(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Asosiy ildiz katalogining breadcrumbs yo'lini qaytaradi."""
    return await FolderService.get_breadcrumbs(db, None)


@router.post("/", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_in: FolderCreate,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Yangi papka (ildizda yoki biror papka ichida) yaratadi."""
    try:
        folder = await FolderService.create_folder(db, folder_in)
        return await FolderService.get_folder_with_stats(db, folder)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{folder_id}", response_model=FolderOut)
async def update_folder(
    folder_id: int,
    folder_in: FolderUpdate,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Papkani nomlash, boshqa papkaga ko'chirish yoki xususiyatlarini yangilash."""
    try:
        updated = await FolderService.update_folder(db, folder_id, folder_in)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Papka topilmadi!")
        return await FolderService.get_folder_with_stats(db, updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Papkani va uning barcha ichki elementlarini (papkalar va fayllarni) butunlay o'chiradi.
    Diskdagi fizik fayllar ham avtomatik tozalanadi.
    """
    success, file_paths = await FolderService.delete_folder(db, folder_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Papka topilmadi!")

    return {
        "success": True,
        "message": f"Papka va unga tegishli {len(file_paths)} ta fayl o'chirildi."
    }
