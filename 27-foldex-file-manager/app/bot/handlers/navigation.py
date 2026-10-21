# -*- coding: utf-8 -*-
"""
Foldex Reply Keyboard Navigatsiya Handleri.
Foydalanuvchi talabi:
- Foydalanuvchi tugmalarni (papka, orqaga) bosganda buyruqlar chatga tushmasin (o'chiriladi).
- Bot ham javob xabarlari yubormasin (chat toza qoladi).
- Reply klaviaturada bosib ketaveradi (klaviatura jimgina yangilanadi).
- Faqat fayl tugmasi bosilganda o'sha fayl chatga yuboriladi.
"""

import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.bot.keyboards.reply import build_folder_reply_keyboard
from app.bot.loader import bot
from app.core.database import async_session_maker
from app.models.file_item import FileItem
from app.services.file_service import FileService
from app.services.folder_service import FolderService
from app.services.telegram_service import TelegramService

router = Router(name="navigation_router")


async def delete_user_message_silently(message: Message) -> None:
    """Foydalanuvchi bosgan xabarni chatda qolmasligi uchun darhol o'chirish."""
    try:
        await message.delete()
    except Exception:
        pass


async def update_reply_keyboard_silently(chat_id: int, keyboard) -> None:
    """
    Chatda hech qanday xabar qoldirmasdan, Reply Keyboardni jimgina yangilaydi.
    Vaqtinchalik xabar yuboriladi va darhol o'chiriladi.
    """
    try:
        temp_msg = await bot.send_message(
            chat_id=chat_id,
            text="‌",  # Ko'rinmas belgi
            reply_markup=keyboard,
            disable_notification=True
        )
        await temp_msg.delete()
    except Exception as e:
        print(f"⚠️ Klaviaturani yangilashda ogohlantirish: {e}")


@router.message(F.text == "⬅️ Orqaga")
async def nav_back(message: Message, state: FSMContext):
    """Bir pog'ona yuqoridagi ota papkaga qaytish."""
    # 1. Foydalanuvchi bosgan xabarni chatdan o'chirish
    await delete_user_message_silently(message)

    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    if not current_folder_id:
        parent_id = None
    else:
        async with async_session_maker() as db:
            current_folder = await FolderService.get_by_id(db, current_folder_id)
            parent_id = current_folder.parent_id if current_folder else None

    await state.update_data(current_folder_id=parent_id)

    async with async_session_maker() as db:
        if parent_id is None:
            # Ildizga qaytish
            root_folders = await FolderService.get_root_folders(db)
            root_files = await FileService.get_files_by_folder(db, None)
            keyboard = build_folder_reply_keyboard(root_folders, root_files, has_parent=False)
        else:
            parent_folder = await FolderService.get_by_id(db, parent_id)
            subfolders = await FolderService.get_subfolders(db, parent_id)
            files = await FileService.get_files_by_folder(db, parent_id)
            has_parent = (parent_folder.parent_id is not None) if parent_folder else False
            keyboard = build_folder_reply_keyboard(subfolders, files, has_parent=has_parent)

    # Bot ham javob bermasin, faqat klaviatura yangilansin
    await update_reply_keyboard_silently(message.chat.id, keyboard)


@router.message(F.text.startswith("📄 "))
async def nav_send_single_file(message: Message, state: FSMContext):
    """
    Reply Keyboarddagi alohida fayl tugmasi bosilganda:
    Foydalanuvchi buyrug'i chatdan o'chiriladi va FAQAT o'sha fayl chatga yuboriladi!
    """
    # 1. Foydalanuvchi bosgan tugma xabarini chatdan o'chirish
    await delete_user_message_silently(message)

    filename = message.text[2:].strip()  # "📄 " belgisini olib tashlash
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        stmt = select(FileItem).where(
            FileItem.name == filename,
            FileItem.folder_id == current_folder_id
        )
        res = await db.execute(stmt)
        file_item = res.scalar_one_or_none()

        # Agar papkadan topilmasa, nomi bo'yicha global qidirish
        if not file_item:
            stmt2 = select(FileItem).where(FileItem.name == filename)
            res2 = await db.execute(stmt2)
            file_item = res2.scalar_one_or_none()

    if not file_item:
        return

    # Faqat faylni chatga yuborish!
    await TelegramService.send_file_to_user(bot, message.chat.id, file_item)


@router.message(F.text == "📤 Hammasini yuborish")
async def nav_send_all(message: Message, state: FSMContext):
    """
    Joriy papkadagi barcha fayllarni birin-ketin chatga jo'natish.
    Buyruq xabari o'chiriladi, ortiqcha matnli xabarlarsiz faqat fayllar yuboriladi.
    """
    await delete_user_message_silently(message)

    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        files = await FileService.get_files_by_folder(db, current_folder_id)

    if not files:
        return

    for file_item in files:
        await TelegramService.send_file_to_user(bot, message.chat.id, file_item)
        await asyncio.sleep(0.3)


@router.message(F.text)
async def nav_folder_click_or_search(message: Message, state: FSMContext):
    """
    Foydalanuvchi papka nomini bosganda:
    - Foydalanuvchi buyrug'i chatga tushmasdan darhol o'chiriladi.
    - Bot hech qanday matnli javob bermaydi.
    - Faqat Reply klaviatura yangilanadi (ichki papkalar va fayllar chiqadi).
    - Foydalanuvchi xohlagancha bosib ketaveradi.
    """
    raw_text = message.text.strip()
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        # 1. Joriy papka ichidagi bolalardan qidiramiz
        subfolders = await FolderService.get_subfolders(db, current_folder_id)

        target_folder = None
        for sf in subfolders:
            if raw_text == f"{sf.icon} {sf.name}" or raw_text == sf.name:
                target_folder = sf
                break

        # 2. Agar joriy papkadan topilmasa, ehtimol ildiz papka nomi bosilgan
        if not target_folder:
            all_root = await FolderService.get_root_folders(db)
            for rf in all_root:
                if raw_text == f"{rf.icon} {rf.name}" or raw_text == rf.name:
                    target_folder = rf
                    break

        # 3. Agar papka topilsa — uning ichiga kirish!
        if target_folder:
            # Foydalanuvchi bosgan xabarni o'chirish (chatga tushmasin!)
            await delete_user_message_silently(message)

            await state.update_data(current_folder_id=target_folder.id)

            new_subfolders = await FolderService.get_subfolders(db, target_folder.id)
            new_files = await FileService.get_files_by_folder(db, target_folder.id)

            keyboard = build_folder_reply_keyboard(new_subfolders, new_files, has_parent=True)

            # Bot javob bermasin, faqat klaviatura yangilansin:
            await update_reply_keyboard_silently(message.chat.id, keyboard)
            return

        # 4. Agar papka topilmasa va bu oddiy matn bo'lsa (qidiruv):
        found_files = await FileService.search_all_files(db, raw_text)
        if found_files:
            await delete_user_message_silently(message)
            # Topilgan fayllarni Reply klaviaturada chiqarish (klaviatura yangilanadi)
            keyboard = build_folder_reply_keyboard([], found_files[:10], has_parent=True)
            await update_reply_keyboard_silently(message.chat.id, keyboard)
        else:
            # Hech narsa topilmasa ham xabarni o'chirish
            await delete_user_message_silently(message)
