# -*- coding: utf-8 -*-
"""
Foldex Reply Keyboard Navigatsiya Handleri.
Foydalanuvchi tugmalarni bosganda papkalar bo'ylab ichma-ich harakatlanish,
orqaga qaytish, fayllarni yuborish va ommaviy yuborish amallarini bajaradi.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

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
        from app.bot.handlers.start import handle_start
        return await handle_start(message, state)

    async with async_session_maker() as db:
        current_folder = await FolderService.get_by_id(db, current_folder_id)
        parent_id = current_folder.parent_id if current_folder else None

        await state.update_data(current_folder_id=parent_id)

        if parent_id is None:
            # Ildizga qaytish
            root_folders = await FolderService.get_root_folders(db)
            root_files = await FileService.get_files_by_folder(db, None)
            keyboard = build_folder_reply_keyboard(root_folders, root_files, has_parent=False)
            text = "🏠 <b>Bosh menyuga qaytildi</b>"
        else:
            parent_folder = await FolderService.get_by_id(db, parent_id)
            subfolders = await FolderService.get_subfolders(db, parent_id)
            files = await FileService.get_files_by_folder(db, parent_id)
            crumbs = await FolderService.get_breadcrumbs(db, parent_id)
            path_str = " / ".join([c.name for c in crumbs])

            keyboard = build_folder_reply_keyboard(subfolders, files, has_parent=(parent_folder.parent_id is not None))
            text = (
                f"{parent_folder.icon} <b>{parent_folder.name}</b>\n"
                f"📍 <i>{path_str}</i>\n\n"
                f"📁 Ichki papkalar: <b>{len(subfolders)}</b> ta\n"
                f"📄 Fayllar: <b>{len(files)}</b> ta"
            )

    await message.answer(text, reply_markup=keyboard)


@router.message(F.text.startswith("📄 "))
async def nav_send_single_file(message: Message, state: FSMContext):
    """Reply Keyboarddagi alohida fayl tugmasi bosilganda uni darhol yuborish."""
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
        return await message.answer("❌ Fayl topilmadi yoki o'chirilgan!")

    await TelegramService.send_file_to_user(bot, message.chat.id, file_item)


@router.message(F.text)
async def nav_folder_click_or_search(message: Message, state: FSMContext):
    """
    Foydalanuvchi papka nomini bosganda ushbu papka ichiga kirish
    yoki matn yuborganda qidiruv amalini bajarish.
    """
    raw_text = message.text.strip()
    data = await state.get_data()
    current_folder_id = data.get("current_folder_id")

    async with async_session_maker() as db:
        # 1. Joriy papka ichidagi bolalardan qidiramiz
        subfolders = await FolderService.get_subfolders(db, current_folder_id)

        target_folder = None
        for sf in subfolders:
            # Emoji bilan yoki emojisiz mos kelishini tekshirish
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
            await state.update_data(current_folder_id=target_folder.id)

            new_subfolders = await FolderService.get_subfolders(db, target_folder.id)
            new_files = await FileService.get_files_by_folder(db, target_folder.id)
            crumbs = await FolderService.get_breadcrumbs(db, target_folder.id)
            path_str = " / ".join([c.name for c in crumbs])

            keyboard = build_folder_reply_keyboard(new_subfolders, new_files, has_parent=True)

            text_lines = [
                f"{target_folder.icon} <b>{target_folder.name}</b>",
                f"📍 <i>{path_str}</i>\n"
            ]
            if target_folder.description:
                text_lines.append(f"ℹ️ {target_folder.description}\n")

            text_lines.append(f"📁 Ichki papkalar: <b>{len(new_subfolders)}</b> ta")
            text_lines.append(f"📄 Fayllar: <b>{len(new_files)}</b> ta")

            if new_files:
                text_lines.append("\n<b>Fayllar ro'yxati:</b>")
                for idx, fl in enumerate(new_files[:15], 1):
                    size_kb = fl.file_size / 1024
                    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                    text_lines.append(f"{idx}. {fl.name} (<code>{size_str}</code>)")
                if len(new_files) > 15:
                    text_lines.append(f"<i>...va yana {len(new_files) - 15} ta fayl</i>")

            await message.answer("\n".join(text_lines), reply_markup=keyboard)
            return

        # 4. Agar papka topilmasa, bu foydalanuvchi yozgan qidiruv so'zi bo'lishi mumkin!
        found_files = await FileService.search_all_files(db, raw_text)
        if found_files:
            text = f"🔍 <b>«{raw_text}» so'rovi bo'yicha {len(found_files)} ta fayl topildi:</b>\n\n"
            for f_item in found_files[:10]:
                text += f"• <b>{f_item.name}</b> (<code>{f_item.file_size / 1024:.1f} KB</code>)\n"
            text += "\n<i>Kerakli faylni jo'natish uchun quyidagi qidiruv natijalaridan foydalaning yoki inline rejimda chaqiring.</i>"

            # Topilgan fayllarni tugma sifatida chiqarish
            keyboard = build_folder_reply_keyboard([], found_files[:6], has_parent=True)
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(
                f"❓ «{raw_text}» bo'yicha papka yoki fayl topilmadi.\n"
                "Navigatsiya uchun klaviatura tugmalaridan foydalaning."
            )
