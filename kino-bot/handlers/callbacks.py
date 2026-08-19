"""Callback query handlerlar: obuna tasdiqlash, guruhga so'rov."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import config
import keyboards as kb
import utils
from .common import send_sub_message, serve_media

router = Router()


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(cq: CallbackQuery, state: FSMContext, bot: Bot):
    check = await utils.check_sub(bot, cq.from_user.id)
    if check is True:
        try:
            await cq.message.delete()
        except Exception:
            pass
        await bot.send_message(
            cq.from_user.id,
            "🎉 <b>Ajoyib! Obunangiz muvaffaqiyatli tasdiqlandi.</b>\n\n"
            "Bizning safimizga qo'shilganingizdan xursandmiz! 😎\n"
            "Endi <b>Kino kodini yuboring</b> va premyeralardan zavqlaning! 🍿",
            reply_markup=kb.main_menu(),
        )
        data = await state.get_data()
        pending = data.get("pending_code")
        if pending:
            await state.update_data(pending_code=None)
            if not await serve_media(bot, cq.from_user.id, pending, state):
                await bot.send_message(cq.from_user.id, f"Kechirasiz, so'ralgan kino (Kod: {pending}) topilmadi.")
    else:
        try:
            await cq.message.delete()
        except Exception:
            pass
        await send_sub_message(bot, cq.from_user.id, check)
    await cq.answer()


@router.callback_query(F.data == "ask_group")
async def ask_group_cb(cq: CallbackQuery, state: FSMContext, bot: Bot):
    if not config.SUPPORT_GROUP:
        await cq.answer()
        return
    data = await state.get_data()
    item = data.get("ask_tmdb_item")
    if not item:
        await cq.answer()
        return
    name = cq.from_user.first_name or "User"
    user_link = f"<a href='tg://user?id={cq.from_user.id}'>{utils.h(name)}</a>"
    poster_html = f"<a href='{item['poster']}'>&#8203;</a>" if item.get("poster") else ""
    overview = (item.get("overview") or "")[:100]
    group_msg = (
        f"❗️ <b>KINO SO'ROVI</b>\n\n👤 {user_link}\n🔎 Nomi: <b>{utils.h(item['name'])}</b>\n"
        f"📄 Tavsif: <i>{utils.h(overview)}...</i>\n\n⚠️ <b>Kimda bo'lsa tashlab bering!</b>\n{poster_html}"
    )
    await bot.send_message(config.SUPPORT_GROUP, group_msg)
    await cq.answer("✅ So'rov guruhga yuborildi!", show_alert=True)

    clean = config.SUPPORT_GROUP.lstrip("@")
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    await bot.send_message(
        cq.from_user.id,
        "Guruhga o‘tish uchun bosing 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🗣 Guruhga o‘tish", url=f"https://t.me/{clean}")]]
        ),
    )
