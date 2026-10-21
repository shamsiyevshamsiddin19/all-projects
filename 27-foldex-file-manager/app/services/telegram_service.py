# -*- coding: utf-8 -*-
"""
Foldex Telegram Xizmati (Telegram Service).
Ushbu modul Telegram Bot API orqali fayllarni foydalanuvchiga yuborish,
veb-panel orqali yuklangan fayllarni Telegram serverlariga sinxronlash
va unikal `telegram_file_id` ni olib saqlash vazifalarini bajaradi.
"""

import os
from pathlib import Path
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.file_item import FileItem


class TelegramService:
    """Telegram bot orqali fayllarni yuborish va file_id ni keshlash xizmati."""

    @staticmethod
    async def sync_file_to_telegram(
        bot: Bot,
        db: AsyncSession,
        file_item: FileItem,
        target_chat_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Diskdagi faylni Telegramga (admin chatiga) yuboradi va olingan
        `telegram_file_id` ni ma'lumotlar bazasida yangilaydi.
        Bu inline rejimda va botda kelgusida ushbu faylni soniyaning
        o'ndan bir ulushida qayta yuklamasdan jo'natish imkonini beradi.
        """
        chat_id = target_chat_id or settings.TELEGRAM_ADMIN_ID
        disk_path = Path(settings.STORAGE_DIR) / file_item.file_path

        if not disk_path.exists():
            return None

        # Agar allaqachon file_id mavjud bo'lsa, qayta yuborish shart emas
        if file_item.telegram_file_id:
            return file_item.telegram_file_id

        try:
            input_file = FSInputFile(str(disk_path), filename=file_item.name)
            caption = f"📁 <b>{file_item.name}</b>\n💾 Hajmi: {file_item.file_size / 1024:.1f} KB"

            # Fayl turiga qarab mos Telegram metodini chaqirish
            if file_item.file_type == "photo":
                msg = await bot.send_photo(chat_id=chat_id, photo=input_file, caption=caption, parse_mode="HTML")
                file_id = msg.photo[-1].file_id
                unique_id = msg.photo[-1].file_unique_id
            elif file_item.file_type == "video":
                msg = await bot.send_video(chat_id=chat_id, video=input_file, caption=caption, parse_mode="HTML")
                file_id = msg.video.file_id
                unique_id = msg.video.file_unique_id
            elif file_item.file_type == "audio":
                msg = await bot.send_audio(chat_id=chat_id, audio=input_file, caption=caption, parse_mode="HTML")
                file_id = msg.audio.file_id
                unique_id = msg.audio.file_unique_id
            else:
                msg = await bot.send_document(chat_id=chat_id, document=input_file, caption=caption, parse_mode="HTML")
                file_id = msg.document.file_id
                unique_id = msg.document.file_unique_id

            # Bazada telegram_file_id ni yangilash
            file_item.telegram_file_id = file_id
            file_item.telegram_file_unique_id = unique_id
            await db.commit()
            return file_id

        except Exception as e:
            # Agar bot tokeni kiritilmagan bo'lsa yoki xatolik yuz bersa
            return None

    @staticmethod
    async def send_file_to_user(
        bot: Bot,
        chat_id: int,
        file_item: FileItem
    ) -> bool:
        """
        Foydalanuvchiga faylni jo'natadi.
        Agar telegram_file_id mavjud bo'lsa, Telegram serveridagi keshdan darhol yuboradi.
        Aks holda diskdan yuklab jo'natadi va file_id ni saqlab qo'yadi.
        """
        caption = f"📁 <b>{file_item.name}</b>"

        try:
            # 1. Keshdagi file_id orqali yuborishga urinish
            if file_item.telegram_file_id:
                if file_item.file_type == "photo":
                    await bot.send_photo(chat_id=chat_id, photo=file_item.telegram_file_id, caption=caption, parse_mode="HTML")
                elif file_item.file_type == "video":
                    await bot.send_video(chat_id=chat_id, video=file_item.telegram_file_id, caption=caption, parse_mode="HTML")
                elif file_item.file_type == "audio":
                    await bot.send_audio(chat_id=chat_id, audio=file_item.telegram_file_id, caption=caption, parse_mode="HTML")
                else:
                    await bot.send_document(chat_id=chat_id, document=file_item.telegram_file_id, caption=caption, parse_mode="HTML")
                return True

            # 2. Diskdan to'g'ridan-to'g'ri yuborish
            disk_path = Path(settings.STORAGE_DIR) / file_item.file_path
            if not disk_path.exists():
                return False

            input_file = FSInputFile(str(disk_path), filename=file_item.name)
            if file_item.file_type == "photo":
                msg = await bot.send_photo(chat_id=chat_id, photo=input_file, caption=caption, parse_mode="HTML")
                file_item.telegram_file_id = msg.photo[-1].file_id
            elif file_item.file_type == "video":
                msg = await bot.send_video(chat_id=chat_id, video=input_file, caption=caption, parse_mode="HTML")
                file_item.telegram_file_id = msg.video.file_id
            elif file_item.file_type == "audio":
                msg = await bot.send_audio(chat_id=chat_id, audio=input_file, caption=caption, parse_mode="HTML")
                file_item.telegram_file_id = msg.audio.file_id
            else:
                msg = await bot.send_document(chat_id=chat_id, document=input_file, caption=caption, parse_mode="HTML")
                file_item.telegram_file_id = msg.document.file_id

            return True

        except Exception:
            return False
