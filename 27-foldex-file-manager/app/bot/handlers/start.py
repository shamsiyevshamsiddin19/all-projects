# -*- coding: utf-8 -*-
"""
Foldex Asosiy Bot Komandalari (/start, /admin, /login, /help).
Foydalanuvchi bilan boshlang'ich muloqotni o'rnatadi,
Reply Keyboard navigatsiyasini ishga tushiradi va veb-panelga
xavfsiz bir martalik kirish havolalarini generatsiya qiladi.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import get_admin_panel_inline_keyboard
from app.bot.keyboards.reply import build_folder_reply_keyboard
from app.core.config import settings
from app.core.database import async_session_maker
from app.core.security import generate_one_time_token
from app.models.auth_token import AdminAuthToken
from app.services.file_service import FileService
from app.services.folder_service import FolderService

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    """
    /start buyrug'i:
    Foydalanuvchi uchun boshlang'ich start xabari va navigatsiya klaviaturasini chiqaradi.
    Bu xabar chatda saqlanib qoladi.
    """
    await state.clear()
    await state.update_data(current_folder_id=None)

    async with async_session_maker() as db:
        root_folders = await FolderService.get_root_folders(db)
        root_files = await FileService.get_files_by_folder(db, None)

    keyboard = build_folder_reply_keyboard(root_folders, root_files, has_parent=False)

    if not root_folders and not root_files:
        hint = (
            "\n\n<i>💡 Hozircha hech qanday papka yaratilmagan.\n"
            "Yangi papka ochish yoki fayllarni yuklash uchun <b>/admin</b> komandasidan "
            "foydalanishingiz yoki botga to'g'ridan-to'g'ri fayl yuborishingiz mumkin.</i>"
        )
    else:
        hint = (
            "\n\nKerakli papkani tanlash uchun quyidagi tugmalardan foydalaning "
            "yoki istalgan chatda <code>@bot_username</code> orqali inline qidiring."
        )

    text = (
        "📂 <b>Foldex — Shaxsiy Fayl Menejeri</b>\n\n"
        "🏠 <b>Joriy joylashuv:</b> <i>Bosh sahifa</i>\n\n"
        f"📁 Papkalar: <b>{len(root_folders)}</b> ta\n"
        f"📄 Fayllar: <b>{len(root_files)}</b> ta"
        f"{hint}"
    )

    await message.answer(text, reply_markup=keyboard)


@router.message(Command("home"))
@router.message(F.text == "🏠 Bosh menyu")
async def handle_home(message: Message, state: FSMContext):
    """
    /home yoki Bosh menyu buyrug'i:
    Foydalanuvchi xabari o'chiriladi, bot yangi xabar yozmasdan klaviaturani
    jimgina bosh sahifa holatiga qaytaradi.
    """
    try:
        await message.delete()
    except Exception:
        pass

    await state.clear()
    await state.update_data(current_folder_id=None)

    async with async_session_maker() as db:
        root_folders = await FolderService.get_root_folders(db)
        root_files = await FileService.get_files_by_folder(db, None)

    keyboard = build_folder_reply_keyboard(root_folders, root_files, has_parent=False)

    from app.bot.handlers.navigation import update_reply_keyboard_silently
    await update_reply_keyboard_silently(message.chat.id, keyboard)


@router.message(Command("search"))
@router.message(F.text == "🔍 Qidiruv")
async def handle_search(message: Message, command: CommandObject = None):
    """
    /search komandasi:
    Fayl va papkalarni nom bo'yicha tezkor qidirish.
    Foydalanish: /search darslik
    """
    query = command.args.strip() if (command and command.args) else ""

    if not query:
        text = (
            "🔍 <b>Fayllarni qidirish</b>\n\n"
            "Qidiruvdan foydalanish uchun:\n"
            "1. <b>Komanda orqali:</b> <code>/search fayl_nomi</code>\n"
            "2. <b>Chatda:</b> Shunchaki fayl yoki papka nomini yozib yuboring\n"
            "3. <b>Inline rejimda:</b> Istalgan chatda <code>@bot_username fayl_nomi</code> deb yozing\n\n"
            "<i>Masalan:</i> <code>/search kitob</code>"
        )
        return await message.answer(text)

    async with async_session_maker() as db:
        found_files = await FileService.search_all_files(db, query)

    if not found_files:
        return await message.answer(
            f"🔍 <b>«{query}»</b> so'rovi bo'yicha hech qanday fayl topilmadi.\n"
            "Bosh sahifaga qaytish uchun: /home"
        )

    text_lines = [
        f"🔍 <b>«{query}» so'rovi bo'yicha {len(found_files)} ta fayl topildi:</b>\n"
    ]
    for idx, fl in enumerate(found_files[:10], 1):
        size_kb = fl.file_size / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        text_lines.append(f"{idx}. <b>{fl.name}</b> (<code>{size_str}</code>)")

    text_lines.append("\n<i>Kerakli faylni jo'natish uchun quyidagi tugmalardan birini bosing:</i>")

    keyboard = build_folder_reply_keyboard([], found_files[:6], has_parent=True)
    await message.answer("\n".join(text_lines), reply_markup=keyboard)


@router.message(Command("clear"))
async def handle_clear(message: Message):
    """
    /clear komandasi:
    Chatdagi barcha xabarlarni tozalaydi, faqat yuborilgan /start xabari saqlanadi.
    """
    from app.services.cleanup_service import CleanupService

    status_msg = await message.answer("🧹 <i>Chat tozalanmoqda...</i>")
    deleted_count = await CleanupService.cleanup_chat_messages(message.bot, message.chat.id)

    report_msg = await message.answer(
        f"🧹 <b>Chat tozalandi!</b>\n\n"
        f"Jami <b>{deleted_count}</b> ta xabar o'chirildi.\n"
        f"<i>Faqat /start xabari saqlab qolindi.</i>"
    )
    # Bildirishnoma xabarlarini ham tozalash
    await asyncio.sleep(4)
    try:
        await status_msg.delete()
        await report_msg.delete()
        await message.delete()
    except Exception:
        pass


@router.message(Command("admin"))
@router.message(F.text == "🌐 Admin Panel")
async def handle_admin(message: Message):
    """
    /admin buyrug'i:
    Talab bo'yicha '🌐 Fayllarni boshqarish' tugmasi bilan https://foldex.shamsiyev.uz
    veb-admin paneliga olib boruvchi tugmani chiqaradi.
    """
    text = (
        "🌐 <b>Foldex Veb-Admin Panel</b>\n\n"
        "Fayllar va papkalarni to'liq boshqarish, yangi papkalar ochish, "
        "kompyuter yoki telefondan fayllarni ko'chirish va yuklash uchun "
        "quyidagi tugmani bosing:\n\n"
        f"🔗 Manzil: <code>{settings.DOMAIN}</code>"
    )

    keyboard = get_admin_panel_inline_keyboard()
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("login"))
async def handle_login(message: Message):
    """
    /login buyrug'i:
    Administrator uchun brauzerda 1 marta bosish bilan parolsiz
    kirish imkonini beruvchi xavfsiz vaqtincha havola yaratadi.
    """
    token_str = generate_one_time_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    async with async_session_maker() as db:
        token_obj = AdminAuthToken(
            token=token_str,
            telegram_user_id=settings.TELEGRAM_ADMIN_ID,
            expires_at=expires,
            is_used=False
        )
        db.add(token_obj)
        await db.commit()

    magic_url = f"{settings.DOMAIN}/auth/verify?token={token_str}"

    text = (
        "🔑 <b>Veb-Admin Panelga Xavfsiz Kirish Havolasi</b>\n\n"
        "Ushbu havola orqali brauzeringizda to'g'ridan-to'g'ri admin panelga kira olasiz:\n\n"
        f"🚀 <a href=\"{magic_url}\"><b>Admin Panelga Kirish (Bosing)</b></a>\n\n"
        f"<i>⚠️ Xavfsizlik eslatmasi: Havola faqat 1 marta va 15 daqiqa davomida amal qiladi.</i>"
    )

    await message.answer(text, disable_web_page_preview=True)


@router.callback_query(F.data == "generate_login_link")
async def handle_callback_login(callback: CallbackQuery):
    """Inline tugma orqali /login havolasini generatsiya qilish."""
    token_str = generate_one_time_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    async with async_session_maker() as db:
        token_obj = AdminAuthToken(
            token=token_str,
            telegram_user_id=settings.TELEGRAM_ADMIN_ID,
            expires_at=expires,
            is_used=False
        )
        db.add(token_obj)
        await db.commit()

    magic_url = f"{settings.DOMAIN}/auth/verify?token={token_str}"

    await callback.message.answer(
        f"🔑 <b>Bir martalik kirish havolasi tayyor:</b>\n\n"
        f"🚀 <a href=\"{magic_url}\"><b>Admin Panelga Kirish (Bosing)</b></a>\n\n"
        f"<i>Amal qilish muddati: 15 daqiqa.</i>",
        disable_web_page_preview=True
    )
    await callback.answer()


@router.message(Command("help"))
async def handle_help(message: Message):
    """Yordam va qo'llanma komandasi."""
    text = (
        "💡 <b>Foldex Foydalanish Bo'yicha Qo'llanma</b>\n\n"
        "<b>Asosiy buyruqlar:</b>\n"
        "• /start yoki /home — Bosh sahifa va papkalar navigatsiyasi\n"
        "• /search [nomi] — Fayl va papkalarni tezkor qidirish\n"
        "• /admin — Veb-admin panelga kirish\n"
        "• /login — Brauzer uchun bir martalik kirish havolasi\n"
        "• /help — Ushbu yordam xabari\n\n"
        "<b>Imkoniyatlar:</b>\n"
        "📂 <i>Papkalar:</i> Klaviatura tugmalari orqali papkalar ichiga kirish va ⬅️ Orqaga qaytish.\n"
        "📤 <i>Hammasini yuborish:</i> Papkadagi barcha fayllarni bir zumda qabul qilish.\n"
        "⚡ <i>Inline Mode:</i> Istalgan guruh yoki chatda <code>@bot_username</code> deb yozib, "
        "papkalarni ko'rish va fayllarni to'g'ridan-to'g'ri jo'natish.\n"
        "⬆️ <i>Fayl yuklash:</i> Botga istalgan faylni tashlasangiz, u joriy papkaga saqlanadi."
    )
    await message.answer(text)
