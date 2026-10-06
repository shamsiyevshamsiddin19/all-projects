"""Foydalanuvchi qismi: start, kod, menyular, qidiruv, reyting, tasodifiy."""
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import config
import db
import keyboards as kb
import tmdb
import utils
from states import UserSG
from .common import send_sub_message, serve_media

router = Router()


def _is_admin(uid: int) -> bool:
    return uid in config.ADMIN_IDS


async def _show_main_menu(bot: Bot, chat_id: int, state: FSMContext):
    await state.clear()
    await bot.send_message(chat_id, "🏠 Bosh menyu", reply_markup=kb.main_menu())


# ---------------- START ----------------
@router.message(CommandStart(deep_link=True))
async def start_deeplink(msg: Message, command: CommandObject, state: FSMContext, bot: Bot):
    await db.register_user(msg.chat.id, msg.from_user.first_name or "", msg.from_user.username or "")
    payload = (command.args or "").strip()

    check = await utils.check_sub(bot, msg.chat.id)
    if check is not True:
        await state.update_data(pending_code=payload)
        await send_sub_message(bot, msg.chat.id, check)
        return
    if not await serve_media(bot, msg.chat.id, payload, state):
        await msg.answer("❌ Kod bo'yicha hech narsa topilmadi.")


@router.message(CommandStart())
async def start(msg: Message, state: FSMContext, bot: Bot):
    await db.register_user(msg.chat.id, msg.from_user.first_name or "", msg.from_user.username or "")

    if _is_admin(msg.chat.id):
        from .admin import show_panel
        await show_panel(msg, state)
        return

    check = await utils.check_sub(bot, msg.chat.id)
    if check is not True:
        await send_sub_message(bot, msg.chat.id, check)
        return

    await state.clear()
    name = msg.from_user.first_name or "Foydalanuvchi"
    welcome = (
        f"👋 <b>Assalomu alaykum, {utils.h(name)}!</b>\n\n"
        "🎬 <b>Sevimli kinolaringiz olamiga xush kelibsiz!</b>\n\n"
        "Bizda:\n✅ Eng so'nggi premyeralar\n✅ Yuqori sifatli seriallar\n"
        "✅ Tezkor qidiruv tizimi mavjud!\n\n"
        "🚀 <b>Boshlash uchun kino kodini yuboring yoki quyidagi tugmalardan birini tanlang:</b>"
    )
    await msg.answer(welcome, reply_markup=kb.main_menu())


# ---------------- ORQAGA / CHIQISH (universal reset) ----------------
@router.message(F.text.in_({"ORQAGA", "CHIQISH", "🏠 MENYU"}))
async def universal_back(msg: Message, state: FSMContext, bot: Bot):
    if _is_admin(msg.chat.id):
        from .admin import show_panel
        await show_panel(msg, state)
        return
    check = await utils.check_sub(bot, msg.chat.id)
    if check is not True:
        await send_sub_message(bot, msg.chat.id, check)
        return
    await _show_main_menu(bot, msg.chat.id, state)


# ---------------- KOD (raqam) ----------------
@router.message(F.text.regexp(r"^\d+$"), ~F.from_user.id.in_(config.ADMIN_IDS))
async def by_code(msg: Message, state: FSMContext, bot: Bot):
    cur = await state.get_state()
    if cur in (UserSG.search_input.state, UserSG.select_result.state, UserSG.view_ep.state):
        # bu holatlarda raqam boshqa maqsadda ishlatiladi — o'tkazib yuboramiz
        return
    check = await utils.check_sub(bot, msg.chat.id)
    if check is not True:
        await state.update_data(pending_code=msg.text)
        await send_sub_message(bot, msg.chat.id, check)
        return
    if not await serve_media(bot, msg.chat.id, msg.text, state):
        await msg.answer("Kod bo'yicha hech narsa topilmadi.")


# ---------------- KOD BILAN QIDIRISH ----------------
@router.message(F.text == "KOD BILAN QIDIRISH")
async def code_prompt(msg: Message, state: FSMContext, bot: Bot):
    if not await _guard(msg, bot):
        return
    await msg.answer("Kino kodini yuboring:", reply_markup=kb.reply_kb([], back=True))


# ---------------- KINOLAR ----------------
@router.message(F.text == "KINOLAR")
async def movies_menu(msg: Message, state: FSMContext, bot: Bot):
    if not await _guard(msg, bot):
        return
    await state.set_state(UserSG.view_mov)
    rows = await db.fetch(
        "SELECT DISTINCT group_name FROM movies WHERE group_name IS NOT NULL AND group_name <> '' ORDER BY group_name ASC LIMIT 50"
    )
    groups = [r["group_name"] for r in rows]
    if not groups:
        rows = await db.fetch("SELECT name FROM movies ORDER BY id ASC LIMIT 50")
        groups = [r["name"] for r in rows]
    await msg.answer(
        "<b>Kino To'plamlar:</b>\nTanlash uchun bosing:",
        reply_markup=kb.reply_kb(groups, back=True),
    )


@router.message(UserSG.view_mov)
async def movies_pick(msg: Message, state: FSMContext, bot: Bot):
    text = msg.text or ""
    group_movies = await db.fetch("SELECT name FROM movies WHERE group_name = $1 ORDER BY code ASC", text)
    if len(group_movies) > 1:
        names = [r["name"] for r in group_movies]
        await msg.answer(f"<b>{utils.h(text)}</b>\nQismni tanlang:", reply_markup=kb.reply_kb(names, back=True))
        return
    m = await db.fetchrow("SELECT * FROM movies WHERE name = $1", text)
    if m:
        await db.execute("UPDATE movies SET views = views + 1 WHERE id = $1", m["id"])
        await bot.send_video(msg.chat.id, m["file_id"], caption=await utils.format_caption(m["name"], m["code"]))
    else:
        await msg.answer("Kino topilmadi.")


# ---------------- SERIALLAR ----------------
@router.message(F.text == "SERIALLAR")
async def series_menu(msg: Message, state: FSMContext, bot: Bot):
    if not await _guard(msg, bot):
        return
    await state.set_state(UserSG.view_ser)
    rows = await db.fetch("SELECT name FROM series ORDER BY id ASC LIMIT 50")
    names = [r["name"] for r in rows]
    await msg.answer("📺 <b>Seriallar:</b>", reply_markup=kb.reply_kb(names, back=True))


@router.message(UserSG.view_ser)
async def series_pick(msg: Message, state: FSMContext, bot: Bot):
    s = await db.fetchrow("SELECT * FROM series WHERE name = $1", msg.text or "")
    if s:
        await state.set_state(UserSG.view_ep)
        await state.update_data(sid=s["id"])
        eps = await db.fetch(
            "SELECT episode_number FROM episodes WHERE series_id = $1 ORDER BY episode_number ASC", s["id"]
        )
        nums = [e["episode_number"] for e in eps]
        await msg.answer("Qism tanlang:", reply_markup=kb.series_episodes_kb(nums))


@router.message(UserSG.view_ep)
async def episode_pick(msg: Message, state: FSMContext, bot: Bot):
    text = msg.text or ""
    data = await state.get_data()
    sid = data.get("sid")

    if text == "BARCHA QISMLAR":
        s = await db.fetchrow("SELECT * FROM series WHERE id = $1", sid)
        eps = await db.fetch("SELECT * FROM episodes WHERE series_id = $1 ORDER BY episode_number ASC", sid)
        if s and eps:
            for ep in eps:
                await bot.send_video(
                    msg.chat.id, ep["file_id"],
                    caption=await utils.format_caption(s["name"], s["code"], ep["episode_number"]),
                )
        return

    num = "".join(ch for ch in text if ch.isdigit())
    if not num:
        return
    ep = await db.fetchrow(
        "SELECT * FROM episodes WHERE series_id = $1 AND episode_number = $2", sid, int(num)
    )
    if ep:
        s = await db.fetchrow("SELECT * FROM series WHERE id = $1", sid)
        if s:
            await db.execute("UPDATE series SET views = views + 1 WHERE id = $1", s["id"])
            await bot.send_video(
                msg.chat.id, ep["file_id"],
                caption=await utils.format_caption(s["name"], s["code"], int(num)),
            )


# ---------------- REYTING VA KODLAR ----------------
@router.message(F.text.in_({"REYTING VA KODLAR", "KODLAR RO'YXATI"}))
async def rating_menu(msg: Message, state: FSMContext, bot: Bot):
    if not await _guard(msg, bot):
        return
    await state.set_state(UserSG.catalog_select)
    await msg.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=kb.reply_kb(["KINOLAR REYTINGI", "SERIALLAR REYTINGI"], back=True),
    )


@router.message(UserSG.catalog_select)
async def rating_list(msg: Message, state: FSMContext, bot: Bot):
    table = "series" if msg.text == "SERIALLAR REYTINGI" else "movies"
    rows = await db.fetch(f"SELECT name, code, views FROM {table} ORDER BY views DESC LIMIT 20")
    if not rows:
        await msg.answer("Ro'yxat bo'sh.")
        return
    out = f"<b>{utils.h(msg.text)}:</b>\n\n"
    buf = out
    i = 1
    for r in rows:
        entry = f'{i}. <a href="{utils.deep_link(r["code"])}">{utils.h(r["name"])}</a> | Kod: {r["code"]}\n'
        if len(buf) + len(entry) > 4000:
            await msg.answer(buf, disable_web_page_preview=True)
            buf = ""
        buf += entry
        i += 1
    if buf:
        await msg.answer(buf, disable_web_page_preview=True)


# ---------------- TASODIFIY KINO (yangi) ----------------
@router.message(F.text == "🎲 TASODIFIY KINO")
async def random_movie(msg: Message, state: FSMContext, bot: Bot):
    if not await _guard(msg, bot):
        return
    m = await db.fetchrow("SELECT * FROM movies ORDER BY random() LIMIT 1")
    if not m:
        await msg.answer("Hozircha kino yo'q.")
        return
    await db.execute("UPDATE movies SET views = views + 1 WHERE id = $1", m["id"])
    await bot.send_video(msg.chat.id, m["file_id"], caption=await utils.format_caption(m["name"], m["code"]))


# ---------------- QIDIRISH ----------------
@router.message(F.text == "QIDIRISH")
async def search_prompt(msg: Message, state: FSMContext, bot: Bot):
    if not await _guard(msg, bot):
        return
    await state.set_state(UserSG.search_input)
    await msg.answer("Kino nomini yozing:", reply_markup=kb.reply_kb([], back=True))


@router.message(UserSG.search_input)
async def search_run(msg: Message, state: FSMContext, bot: Bot):
    await perform_search(bot, msg.chat.id, msg.text or "", state)


@router.message(UserSG.select_result)
async def search_select(msg: Message, state: FSMContext, bot: Bot):
    text = msg.text or ""
    if not text.isdigit():
        # yangi qidiruv
        await state.set_state(UserSG.search_input)
        await perform_search(bot, msg.chat.id, text, state)
        return
    data = await state.get_data()
    results = data.get("search_results", [])
    num = int(text)
    if not (1 <= num <= len(results)):
        await msg.answer("Noto'g'ri raqam.")
        return
    item = results[num - 1]

    if item["source"] == "local":
        if item["type"] == "movie":
            await db.execute("UPDATE movies SET views = views + 1 WHERE id = $1", item["id"])
            await bot.send_video(
                msg.chat.id, item["file_id"],
                caption=await utils.format_caption(item["name"], item["code"]),
            )
        else:
            await db.execute("UPDATE series SET views = views + 1 WHERE id = $1", item["id"])
            await state.set_state(UserSG.view_ep)
            await state.update_data(sid=item["id"])
            eps = await db.fetch(
                "SELECT episode_number FROM episodes WHERE series_id = $1 ORDER BY episode_number ASC", item["id"]
            )
            nums = [e["episode_number"] for e in eps]
            await msg.answer(
                f"Serial: <b>{utils.h(item['name'])}</b>\nQismni tanlang:",
                reply_markup=kb.series_episodes_kb(nums),
            )
    else:
        await state.update_data(ask_tmdb_item=item)
        caption = (
            f"<b>{utils.h(item['name'])}</b>\n\n<i>{utils.h(item['overview'])}</i>\n\n"
            "⚠️ <b>Bot bazasida yo'q.</b> Internetdan topildi."
        )
        if item.get("poster"):
            await bot.send_photo(msg.chat.id, item["poster"], caption=caption, reply_markup=kb.web_buttons(item["name"]))
        else:
            await bot.send_message(msg.chat.id, caption, reply_markup=kb.web_buttons(item["name"]))


async def perform_search(bot: Bot, chat_id: int, text: str, state: FSMContext):
    await bot.send_chat_action(chat_id, "typing")
    query = utils.normalize_search_text(text)
    results = []
    if query:
        like = f"%{query}%"
        rows = await db.fetch(
            """(SELECT id, code, name, file_id, 'movie' AS type, 'local' AS source
                  FROM movies WHERE lower(name) LIKE $1 LIMIT 10)
               UNION ALL
               (SELECT id, code, name, NULL AS file_id, 'series' AS type, 'local' AS source
                  FROM series WHERE lower(name) LIKE $1 LIMIT 10)""",
            like,
        )
        results = [dict(r) for r in rows]

    if len(results) < 5:
        results += await tmdb.search(text)

    if not results:
        grp = config.SUPPORT_GROUP or "@Tarjimakinolargr"
        grp_link = "https://t.me/" + grp.lstrip("@")
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👥 Guruhga o'tish", url=grp_link)]])
        await bot.send_message(
            chat_id,
            "🤷‍♂️ <b>Hech narsa topilmadi.</b>\n\n⚠️ <i>Kino nomini to'g'ri yozganingizga ishonch hosil qiling!</i>\n\n"
            f"Botdan topa olmagan bo'lsangiz, <b>{utils.h(grp)}</b> guruhimizga o'tib so'rashingiz mumkin.",
            reply_markup=btn,
        )
        return

    results = results[:10]
    await state.update_data(search_results=results)

    out = "<b>Qidiruv natijalari:</b>\n\n"
    row, kbd = [], []
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    for i, item in enumerate(results, 1):
        icon = "📺" if item["type"] in ("series", "tv") else "🎬"
        src = "🤖" if item["source"] == "local" else "🌐"
        year = f" ({item['year']})" if item.get("year") else ""
        out += f"<b>{i}.</b> {icon} {utils.h(item['name'])}{year} {src}\n"
        row.append(KeyboardButton(text=str(i)))
        if len(row) == 5:
            kbd.append(row)
            row = []
    if row:
        kbd.append(row)
    kbd.append([KeyboardButton(text="ORQAGA")])

    await state.set_state(UserSG.select_result)
    await bot.send_message(chat_id, out, reply_markup=ReplyKeyboardMarkup(keyboard=kbd, resize_keyboard=True))


# /help
@router.message(Command("help"))
async def help_cmd(msg: Message):
    await msg.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "• Kino <b>kodini</b> yuboring — darhol olasiz\n"
        "• <b>KINOLAR / SERIALLAR</b> — to'plamlar\n"
        "• <b>QIDIRISH</b> — nomi bo'yicha izlash\n"
        "• <b>REYTING VA KODLAR</b> — eng ommabop kinolar\n"
        "• <b>🎲 TASODIFIY KINO</b> — tasodifiy tanlov\n\n"
        f"Inline: istalgan chatda <code>@{config.BOT_USERNAME} kino nomi</code> deb yozing."
    )


# ---------------- yordamchi: obuna gate ----------------
async def _guard(msg: Message, bot: Bot) -> bool:
    if _is_admin(msg.chat.id):
        return True
    check = await utils.check_sub(bot, msg.chat.id)
    if check is not True:
        await send_sub_message(bot, msg.chat.id, check)
        return False
    return True
