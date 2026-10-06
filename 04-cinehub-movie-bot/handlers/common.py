"""Bir nechta handlerda ishlatiladigan umumiy logika."""
from aiogram import Bot
from aiogram.fsm.context import FSMContext

import db
import keyboards as kb
import utils
from states import UserSG


async def send_sub_message(bot: Bot, chat_id: int, missing):
    text = (
        "🔒 <b>Botdan to'liq foydalanish uchun obuna bo'lishingiz kerak.</b>\n\n"
        "Hurmatli foydalanuvchi, bizning mehnatimizni qadrlagan holda quyidagi "
        "kanallarga obuna bo'lishingizni so'raymiz. Bu bizga yangi kinolarni "
        "yuklashda yordam beradi! 🚀\n\n"
        "👇 <b>Kanallarga a'zo bo'lib, TASDIQLASH tugmasini bosing:</b>"
    )
    await bot.send_message(chat_id, text, reply_markup=await kb.sub_message_kb(missing))


async def serve_media(bot: Bot, chat_id: int, code, state: FSMContext) -> bool:
    """Kod bo'yicha kino yoki serialni yuborish. True — topildi."""
    code = str(code).replace("code_", "").strip()
    if not code.lstrip("-").isdigit():
        return False
    code_int = int(code)

    movie = await db.fetchrow("SELECT * FROM movies WHERE code = $1", code_int)
    if movie:
        await db.execute("UPDATE movies SET views = views + 1 WHERE id = $1", movie["id"])
        await bot.send_video(
            chat_id,
            movie["file_id"],
            caption=await utils.format_caption(movie["name"], movie["code"]),
        )
        return True

    ser = await db.fetchrow("SELECT * FROM series WHERE code = $1", code_int)
    if ser:
        await db.execute("UPDATE series SET views = views + 1 WHERE id = $1", ser["id"])
        await state.set_state(UserSG.view_ep)
        await state.update_data(sid=ser["id"])
        eps = await db.fetch(
            "SELECT episode_number FROM episodes WHERE series_id = $1 ORDER BY episode_number ASC",
            ser["id"],
        )
        nums = [e["episode_number"] for e in eps]
        await bot.send_message(
            chat_id,
            f"Serial: <b>{utils.h(ser['name'])}</b>\nQism tanlang:",
            reply_markup=kb.series_episodes_kb(nums),
        )
        return True

    return False
