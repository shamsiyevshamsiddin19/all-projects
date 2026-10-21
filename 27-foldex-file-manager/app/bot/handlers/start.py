# -*- coding: utf-8 -*-
"""
Foldex Asosiy Bot Komandalari (/start, /admin, /login, /help).
Foydalanuvchi bilan boshlang'ich muloqotni o'rnatadi,
Reply Keyboard navigatsiyasini ishga tushiradi va veb-panelga
xavfsiz bir martalik kirish havolalarini generatsiya qiladi.
"""

from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
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
    Navigatsiya holatini asosiy (ildiz) papkaga qaytaradi va
    asosiy papkalar ro'yxatini Reply Keyboard tugmalari sifatida chiqaradi.
    """
    await state.clear()
    await state.update_data(current_folder_id=None)

    async with async_session_maker() as db:
        root_folders = await FolderService.get_root_folders(db)
        root_files = await FileService.get_files_by_folder(db, None)

    keyboard = build_folder_reply_keyboard(root_folders, root_files, has_parent=False)

    text = (
        "📂 <b>Foldex — Shaxsiy Fayl Menejeri</b>\n\n"
        "🏠 <b>Joriy joylashuv:</b> <i>Bosh sahifa</i>\n\n"
        f"📁 Papkalar: <b>{len(root_folders)}</b> ta\n"
        f"📄 Fayllar: <b>{len(root_files)}</b> ta\n\n"
        "Kerakli papkani tanlash uchun quyidagi tugmalardan foydalaning "
        "yoki istalgan chatda <code>@bot_username</code> orqali inline qidiring."
    )

    await message.answer(text, reply_markup=keyboard)


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
        "• /start — Bosh sahifa va papkalar navigatsiyasi\n"
        "• /admin — Veb-admin panel havolasi\n"
        "• /login — Brauzer uchun bir martalik kirish havolasi\n"
        "• /help — Ushbu yordam xabari\n\n"
        "<b>Imkoniyatlar:</b>\n"
        "📂 <i>Reply Keyboard:</i> Tugmalar orqali cheksiz ichki papkalarga kirish va qaytish.\n"
        "📤 <i>Hammasini yuborish:</i> Papkadagi barcha fayllarni bir zumda qabul qilish.\n"
        "⚡ <i>Inline Mode:</i> Istalgan guruh yoki chatda <code>@bot_username</code> deb yozib, "
        "papkalarni ko'rish va fayllarni to'g'ridan-to'g'ri jo'natish.\n"
        "⬆️ <i>Fayl yuklash:</i> Botga istalgan faylni tashlasangiz, u joriy papkaga saqlanadi."
    )
    await message.answer(text)
