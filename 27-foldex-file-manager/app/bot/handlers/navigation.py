# -*- coding: utf-8 -*-
"""
Foldex Reply Keyboard Navigatsiya Handleri.
Foydalanuvchi tugmalarni bosganda papkalar bo'ylab ichma-ich harakatlanish,
orqaga qaytish, fayllarni yuborish va ommaviy yuborish amallarini bajaradi.
Xabarlar darhol o'chirilmaydi, har 5-chi buyruq bosilganda oldingi xabarlar
tracker middleware orqali avtomatik tarzda tozalanadi.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import func, select

from app.bot.keyboards.reply import build_folder_reply_keyboard
from app.bot.loader import bot
from app.core.database import async_session_maker
from app.models.file_item import FileItem
from app.models.folder import Folder
from app.services.file_service import FileService
from app.services.folder_service import FolderService
from app.services.telegram_service import TelegramService

router = Router(name="navigation_router")


@router.message(F.text == "⬅️ Orqaga")
async def nav_back(message: Message, state: FSMContext):
    """Bir pog'ona yuqoridagi ota papkaga qaytish."""
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
            root_folders = await FolderService.get_root_folders(db)
            root_files = await FileService.get_files_by_folder(db, None)
            keyboard = build_folder_reply_keyboard(root_folders, root_files, has_parent=False)
            text = "📂 <code>/</code>"
        else:
            parent_folder = await FolderService.get_by_id(db, parent_id)
            subfolders = await FolderService.get_subfolders(db, parent_id)
            files = await FileService.get_files_by_folder(db, parent_id)
            path_str = await FolderService.get_path_string(db, parent_id)
            has_parent = (parent_folder.parent_id is not None) if parent_folder else False

            keyboard = build_folder_reply_keyboard(subfolders, files, has_parent=has_parent)
            text = f"📂 <code>{path_str}</code>"

    await message.answer(text, reply_markup=keyboard)


@router.message(F.text.startswith("📄 "))
async def nav_send_single_file(message: Message, state: FSMContext):
    """Reply Keyboarddagi alohida fayl tugmasi bosilganda uni darhol yuborish."""
    filename = message.text[2:].strip()
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        stmt = select(FileItem).where(
            FileItem.name == filename,
            FileItem.folder_id == current_folder_id
        )
        res = await db.execute(stmt)
        file_item = res.scalar_one_or_none()

        if not file_item:
            stmt2 = select(FileItem).where(FileItem.name == filename)
            res2 = await db.execute(stmt2)
            file_item = res2.scalar_one_or_none()

    if not file_item:
        return await message.answer("❌ Fayl topilmadi yoki o'chirilgan!")

    await TelegramService.send_file_to_user(bot, message.chat.id, file_item)


@router.message(F.text == "📤 Hammasini yuborish")
async def nav_send_all(message: Message, state: FSMContext):
    """Joriy papkadagi barcha fayllarni birin-ketin chatga jo'natish."""
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        files = await FileService.get_files_by_folder(db, current_folder_id)

    if not files:
        return await message.answer("ℹ️ Ushbu papkada fayl mavjud emas.")

    status_msg = await message.answer(f"⏳ <b>{len(files)}</b> ta fayl yuborilmoqda...")
    sent = 0
    for file_item in files:
        success = await TelegramService.send_file_to_user(bot, message.chat.id, file_item)
        if success:
            sent += 1

    await status_msg.edit_text(f"✅ Jami <b>{sent}</b> ta fayl muvaffaqiyatli jo'natildi!")


@router.message(F.text)
async def nav_folder_click_or_search(message: Message, state: FSMContext):
    """
    Foydalanuvchi papka nomini bosganda yoki yo'lini kiritganda (/rus tili/kitob)
    ichiga kirib uning yo'lini qaytaradi, aks holda qidiruv o'tkazadi.
    """
    raw_text = message.text.strip()
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        target_folder = None

        # 1. Joriy papkaning bevosita ichki papkalari orasidan qidirish
        subfolders = await FolderService.get_subfolders(db, current_folder_id)
        for sf in subfolders:
            if raw_text == f"{sf.icon} {sf.name}" or raw_text == sf.name:
                target_folder = sf
                break

        # 2. Ildiz papkalar orasidan qidirish
        if not target_folder:
            all_root = await FolderService.get_root_folders(db)
            for rf in all_root:
                if raw_text == f"{rf.icon} {rf.name}" or raw_text == rf.name:
                    target_folder = rf
                    break

        # 3. Agar to'liq yoki nisbiy yo'l ko'rinishida yozilgan bo'lsa (masalan: "/rus tili/kitob")
        if not target_folder and ("/" in raw_text or raw_text.startswith("/")):
            target_folder = await FolderService.get_folder_by_path(db, raw_text)

        # 4. Istalgan boshqa papka nomi bo'yicha qidirish
        if not target_folder:
            clean_name = raw_text.lstrip("📁 ").strip()
            stmt = select(Folder).where(func.lower(Folder.name) == clean_name.lower())
            res = await db.execute(stmt)
            target_folder = res.scalars().first()

        # Agar papka topilsa, o'sha papkaga o'tib yo'lini qaytaramiz
        if target_folder:
            await state.update_data(current_folder_id=target_folder.id)

            new_subfolders = await FolderService.get_subfolders(db, target_folder.id)
            new_files = await FileService.get_files_by_folder(db, target_folder.id)
            path_str = await FolderService.get_path_string(db, target_folder.id)

            keyboard = build_folder_reply_keyboard(new_subfolders, new_files, has_parent=True)

            text = f"📂 <code>{path_str}</code>"
            if target_folder.description:
                text += f"\n<i>ℹ️ {target_folder.description}</i>"

            await message.answer(text, reply_markup=keyboard)
            return

        # Agar papka topilmasa, bu qidiruv so'rovi bo'lishi mumkin
        found_files = await FileService.search_all_files(db, raw_text)
        if found_files:
            text = f"🔍 <b>«{raw_text}» bo'yicha {len(found_files)} ta fayl topildi:</b>\n"
            for f_item in found_files[:10]:
                text += f"• <b>{f_item.name}</b> (<code>{f_item.file_size / 1024:.1f} KB</code>)\n"
            keyboard = build_folder_reply_keyboard([], found_files[:6], has_parent=True)
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(
                f"❓ «{raw_text}» bo'yicha papka yoki fayl topilmadi.\n"
                "Navigatsiya uchun klaviatura tugmalaridan foydalanishingiz yoki /home deb yozishingiz mumkin."
            )
