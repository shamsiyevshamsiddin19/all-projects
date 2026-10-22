# -*- coding: utf-8 -*-
"""
Foldex Fayllar API yo'llari (Files API).
Fayllarni yuklash (yakka va ommaviy), ro'yxatini olish,
qidirish, yuklab olish, qayta nomlash, ko'chirish va o'chirish amallari.
Barcha amallar faqat TELEGRAM_ADMIN_ID (7883409434) uchun ochiq.
"""

from pathlib import Path
from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.file_item import FileItem
from app.schemas.file_item import FileItemOut, FileItemUpdate, FileListResponse
from app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["Fayllar"])


@router.get("/", response_model=FileListResponse)
async def list_files(
    folder_id: Optional[int] = Query(None, description="Papka ID si"),
    search: Optional[str] = Query(None, description="Qidiruv so'zi"),
    file_type: Optional[str] = Query(None, description="Fayl turi filtri (photo, video, document, etc.)"),
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Tanlangan papkadagi fayllar ro'yxatini filtrlar bilan qaytaradi."""
    if search and folder_id is None:
        # Butun baza bo'ylab global qidiruv
        files = await FileService.search_all_files(db, search)
    else:
        files = await FileService.get_files_by_folder(db, folder_id, search, file_type)

    items = [FileService.to_schema(f) for f in files]
    return FileListResponse(total=len(items), items=items)


@router.post("/upload", response_model=List[FileItemOut], status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: List[UploadFile] = File(..., description="Bir yoki bir nechta yuklanayotgan fayllar"),
    folder_id: Optional[int] = Form(None, description="Joylashtiriladigan papka ID si"),
    description: Optional[str] = Form(None, description="Fayllar uchun ixtiyoriy tavsif"),
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Bir vaqtning o'zida bir nechta faylni yuklash imkoniyati (Batch Upload).
    Fayllar xavfsiz nomlanib, diskka oqimli (chunked) yoziladi.
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hech qanday fayl tanlanmagan!")

    saved_items: List[FileItemOut] = []

    for file in files:
        if not file.filename:
            continue
        try:
            file_item = await FileService.save_upload(
                db=db,
                file=file,
                folder_id=folder_id,
                description=description
            )
            saved_items.append(FileService.to_schema(file_item))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Faylni yuklashda xatolik yuz berdi: {str(e)}"
            )

    return saved_items


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    inline: bool = Query(False, description="true bo'lsa brauzerda ochiladi (ko'rish oynasi uchun)"),
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Faylni original nomi bilan yuklab olish yoki brauzerda ochish."""
    file_item = await FileService.get_by_id(db, file_id)
    if not file_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fayl topilmadi!")

    disk_path = Path(settings.STORAGE_DIR) / file_item.file_path
    if not disk_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fayl server diskida topilmadi!")

    # UTF-8 belgilarni (o'zbekcha harflar) to'g'ri uzatish.
    # inline=true bo'lganda brauzer faylni yuklab olmasdan o'zida ochadi —
    # PDF va rasmlarni ko'rish oynasi shunga tayanadi.
    encoded_filename = quote(file_item.name)
    disposition_type = "inline" if inline else "attachment"
    content_disposition = f"{disposition_type}; filename*=UTF-8''{encoded_filename}"

    return FileResponse(
        path=str(disk_path),
        media_type=file_item.mime_type,
        headers={"Content-Disposition": content_disposition}
    )


@router.post("/{file_id}/send-telegram")
async def send_file_to_telegram(
    file_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Faylni administratorning Telegram chatiga jo'natadi.
    Fayl avval yuborilgan bo'lsa, Telegram keshidagi file_id orqali
    lahzalik ketadi — server diskidan qayta yuklanmaydi.
    """
    file_item = await FileService.get_by_id(db, file_id)
    if not file_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fayl topilmadi!")

    from app.bot.loader import bot
    from app.services.telegram_service import TelegramService

    try:
        sent = await TelegramService.send_file_to_user(
            bot=bot, chat_id=settings.TELEGRAM_ADMIN_ID, file_item=file_item
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegramga jo'natishda xatolik: {str(e)[:150]}"
        )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Fayl jo'natilmadi (diskda topilmadi yoki bot javob bermadi)."
        )

    await db.commit()
    return {"ok": True, "detail": f"«{file_item.name}» Telegramga jo'natildi."}


@router.put("/{file_id}", response_model=FileItemOut)
async def update_file(
    file_id: int,
    file_in: FileItemUpdate,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Fayl nomini o'zgartirish yoki boshqa papkaga ko'chirish."""
    try:
        updated = await FileService.update_file(db, file_id, file_in)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fayl topilmadi!")
        return FileService.to_schema(updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Faylni server diskidan va bazadan to'liq o'chiradi."""
    success = await FileService.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fayl topilmadi!")
    return {"success": True, "message": "Fayl muvaffaqiyatli o'chirildi."}
