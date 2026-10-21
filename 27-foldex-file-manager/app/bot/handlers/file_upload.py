# -*- coding: utf-8 -*-
"""
Foldex Telegram orqali fayl yuklash handleri.
Admin chat orqali botga to'g'ridan-to'g'ri hujjat (document),
rasm (photo), video yoki audio yuborganda, uni serverga yuklab oladi,
ma'lumotlar bazasiga joriy papka bilan bog'lab saqlaydi va telegram_file_id ni keshlaydi.
"""

from pathlib import Path
import uuid
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.loader import bot
from app.core.config import settings
from app.core.database import async_session_maker
from app.core.security import sanitize_filename
from app.models.file_item import FileItem
from app.schemas.file_item import format_bytes
from app.services.file_service import FileService
from app.services.folder_service import FolderService

router = Router(name="file_upload_router")


@router.message(F.document | F.photo | F.video | F.audio)
async def handle_direct_file_upload(message: Message, state: FSMContext):
    """Admin botga fayl yuborganda uni qabul qilish va saqlash."""
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    # 1. Fayl turi va metama'lumotlarini aniqlash
    file_id = None
    unique_id = None
    file_name = None
    file_size = 0
    mime_type = "application/octet-stream"

    if message.document:
        doc = message.document
        file_id = doc.file_id
        unique_id = doc.file_unique_id
        file_name = doc.file_name or f"hujjat_{int(message.date.timestamp())}.bin"
        file_size = doc.file_size or 0
        mime_type = doc.mime_type or "application/octet-stream"
    elif message.photo:
        photo = message.photo[-1]  # Eng yuqori sifatlisi
        file_id = photo.file_id
        unique_id = photo.file_unique_id
        file_name = f"rasm_{int(message.date.timestamp())}.jpg"
        file_size = photo.file_size or 0
        mime_type = "image/jpeg"
    elif message.video:
        vid = message.video
        file_id = vid.file_id
        unique_id = vid.file_unique_id
        file_name = vid.file_name or f"video_{int(message.date.timestamp())}.mp4"
        file_size = vid.file_size or 0
        mime_type = vid.mime_type or "video/mp4"
    elif message.audio:
        aud = message.audio
        file_id = aud.file_id
        unique_id = aud.file_unique_id
        file_name = aud.file_name or f"audio_{int(message.date.timestamp())}.mp3"
        file_size = aud.file_size or 0
        mime_type = aud.mime_type or "audio/mpeg"

    if not file_id:
        return await message.answer("❌ Fayl ma'lumotlarini o'qib bo'lmadi.")

    status_msg = await message.answer(f"⏳ «{file_name}» qabul qilinmoqda...")

    try:
        # 2. Xavfsiz nom yaratish va diskka yuklab olish
        safe_name = sanitize_filename(file_name)
        ext = Path(safe_name).suffix.lower()
        stored_filename = f"{uuid.uuid4().hex}{ext}"

        storage_dir = Path(settings.STORAGE_DIR)
        storage_dir.mkdir(parents=True, exist_ok=True)
        disk_path = storage_dir / stored_filename

        # Telegram Bot API orqali faylni server diskiga yuklab olish
        tg_file = await bot.get_file(file_id)
        if tg_file.file_path:
            await bot.download_file(tg_file.file_path, destination=disk_path)

        # Haqiqiy hajmni aniqlash
        if disk_path.exists():
            file_size = disk_path.stat().st_size

        file_type = FileService.detect_file_type(safe_name, mime_type)

        # 3. Ma'lumotlar bazasiga yozish
        async with async_session_maker() as db:
            folder_name = "Bosh sahifa"
            if current_folder_id:
                folder_obj = await FolderService.get_by_id(db, current_folder_id)
                if folder_obj:
                    folder_name = folder_obj.name

            file_item = FileItem(
                name=safe_name,
                folder_id=current_folder_id,
                stored_filename=stored_filename,
                file_path=stored_filename,
                file_size=file_size,
                mime_type=mime_type,
                file_type=file_type,
                telegram_file_id=file_id,
                telegram_file_unique_id=unique_id,
                description=message.caption
            )
            db.add(file_item)
            await db.commit()

        await status_msg.edit_text(
            f"✅ <b>Fayl muvaffaqiyatli saqlandi!</b>\n\n"
            f"📄 Nomi: <b>{safe_name}</b>\n"
            f"💾 Hajmi: <b>{format_bytes(file_size)}</b>\n"
            f"📁 Papka: <b>{folder_name}</b>\n"
            f"⚡ <i>Telegram file_id keshlandi va veb-panelda aks etdi.</i>"
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ Faylni saqlashda xatolik yuz berdi: {str(e)}")
