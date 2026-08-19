"""Telegram admin paneli: kino/serial qo'shish, rename, o'chirish, obuna,
ijtimoiy tarmoqlar, statistika, reklama.

Kontent (video file_id) faqat Telegram orqali qo'shiladi — shu sabab bu panel
web-admin bilan birga saqlanadi."""
import asyncio

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

import config
import db
import keyboards as kb
import utils
from states import AdminSG

router = Router()
router.message.filter(F.from_user.id.in_(config.ADMIN_IDS))


# ------------------------------------------------------------------ panel
async def show_panel(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.panel)
    await msg.answer("👑 <b>Admin Panel</b>", reply_markup=kb.admin_menu())


# ------------------------------------------------------------------ kanal post yordamchisi
async def post_to_channel(bot: Bot, admin_id: int, file_id: str, caption: str, target: str) -> bool:
    if not target or (not target.startswith("@") and not target.lstrip("-").isdigit()):
        return False
    try:
        await bot.send_video(target, file_id, caption=caption)
        return True
    except Exception:
        if target == config.UPLOAD_CHANNEL:
            await bot.send_message(
                admin_id,
                f"❌ <b>Xatolik:</b> Bot asosiy kanalga ({utils.h(target)}) post yozolmadi. "
                "Botni kanalga Admin qiling!",
            )
        return False


def _detect_platform(url: str) -> str:
    u = url.lower()
    table = [
        ("instagram.com", "Instagram"), ("tiktok.com", "TikTok"),
        ("youtube.com", "YouTube"), ("youtu.be", "YouTube"),
        ("facebook.com", "Facebook"), ("fb.com", "Facebook"),
        ("twitter.com", "X (Twitter)"), ("x.com", "X (Twitter)"),
        ("t.me", "Telegram"), ("telegram.me", "Telegram"),
    ]
    for needle, name in table:
        if needle in u:
            return name
    return "Website"


# ================================================================== MENU ROUTER
@router.message(AdminSG.panel, F.text == "KINO QO'SHISH")
async def m_add_movie(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.movie_add_type)
    await msg.answer("Turini tanlang:", reply_markup=kb.reply_kb(["YANGI KINO", "MAVJUD KINOGA QO'SHISH"]))


@router.message(AdminSG.panel, F.text == "SERIAL QO'SHISH")
async def m_add_series(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.series_add_type)
    await msg.answer("Turini tanlang:", reply_markup=kb.reply_kb(["YANGI SERIAL", "QISM QO'SHISH"]))


@router.message(AdminSG.panel, F.text == "O'CHIRISH")
async def m_delete(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.del_choice)
    await msg.answer("Nimani o'chirasiz?", reply_markup=kb.reply_kb(["KINO", "SERIAL"]))


@router.message(AdminSG.panel, F.text == "KINO NOMINI O'ZGARTIRISH")
async def m_rename_movie(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.mov_rename_browser)
    await state.update_data(list_filter=None, list_page=0)
    rows = await db.fetch("SELECT name FROM movies ORDER BY id DESC LIMIT 500")
    await _send_list(msg, state, [r["name"] for r in rows], "O'zgartirish uchun kinoni tanlang:")


@router.message(AdminSG.panel, F.text == "SERIAL NOMINI O'ZGARTIRISH")
async def m_rename_series(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.ser_rename_browser)
    await state.update_data(list_filter=None, list_page=0)
    rows = await db.fetch("SELECT name FROM series ORDER BY id DESC")
    await _send_list(msg, state, [r["name"] for r in rows], "O'zgartirish uchun serialni tanlang:")


@router.message(AdminSG.panel, F.text == "STATISTIKA")
async def m_stats(msg: Message):
    u = await db.fetchval("SELECT COUNT(*) FROM users")
    m = await db.fetchval("SELECT COUNT(*) FROM movies")
    s = await db.fetchval("SELECT COUNT(*) FROM series")
    sl = await db.fetchval("SELECT COUNT(*) FROM social_links")
    vm = await db.fetchval("SELECT COALESCE(SUM(views),0) FROM movies")
    vs = await db.fetchval("SELECT COALESCE(SUM(views),0) FROM series")
    await msg.answer(
        "📊 <b>STATISTIKA:</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{u}</b>\n"
        f"🎬 Kinolar: <b>{m}</b>\n"
        f"📺 Seriallar: <b>{s}</b>\n"
        f"👁 Jami ko'rishlar: <b>{int(vm) + int(vs)}</b>\n"
        f"🔗 Ijtimoiy havolalar: <b>{sl}</b>"
    )


@router.message(AdminSG.panel, F.text == "MANBA SOZLAMALARI")
async def m_source(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.set_sig)
    await msg.answer("Post tagiga qo'yiladigan manbani yuboring (Masalan: @kanalim):", reply_markup=kb.reply_kb([]))


@router.message(AdminSG.panel, F.text == "OBUNA SOZLAMALARI")
async def m_sub(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.sub_sets)
    await msg.answer("Tanlang:", reply_markup=kb.reply_kb(["YOQISH", "O'CHIRISH", "KANAL QO'SHISH", "KANAL O'CHIRISH"]))


@router.message(AdminSG.panel, F.text == "IJTIMOIY TARMOQLAR")
async def m_social(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.social_menu)
    await msg.answer("Ijtimoiy tarmoqlar bo'limi:", reply_markup=kb.reply_kb(["➕ QO'SHISH", "📋 RO'YXAT", "🗑 O'CHIRISH"]))


@router.message(AdminSG.panel, F.text == "REKLAMA")
async def m_broadcast(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.broad_collect)
    await state.update_data(broad_list=[])
    await msg.answer(
        "Reklama postlarini yuboring (Matn, Rasm, Video, Albom).\nTugatgach <b>BOSHLASH</b> ni bosing.",
        reply_markup=kb.reply_kb(["BOSHLASH", "BEKOR QILISH"]),
    )


# ================================================================== list helper
async def _send_list(msg: Message, state: FSMContext, items, title):
    data = await state.get_data()
    page = data.get("list_page", 0)
    markup, page, total = kb.list_keyboard(items, page)
    await state.update_data(list_page=page)
    await msg.answer(f"{title}\n(Sahifa: {page + 1}/{total})", reply_markup=markup)


# ================================================================== KINO QO'SHISH
@router.message(AdminSG.movie_add_type, F.text == "YANGI KINO")
async def new_movie(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.add_movie_name)
    await msg.answer("Kino nomi:", reply_markup=kb.reply_kb([]))


@router.message(AdminSG.movie_add_type, F.text == "MAVJUD KINOGA QO'SHISH")
async def existing_movie(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.mov_group_browser)
    await state.update_data(list_filter=None, list_page=0)
    rows = await db.fetch(
        "SELECT DISTINCT group_name FROM movies WHERE group_name IS NOT NULL AND group_name <> '' ORDER BY group_name ASC"
    )
    await _send_list(msg, state, [r["group_name"] for r in rows], "Qaysi kinoga qo'shasiz? Tanlang:")


async def _movie_groups(filter_):
    if filter_:
        rows = await db.fetch(
            "SELECT DISTINCT group_name FROM movies WHERE group_name IS NOT NULL AND group_name <> '' AND group_name ILIKE $1 ORDER BY group_name ASC",
            f"%{filter_}%",
        )
    else:
        rows = await db.fetch(
            "SELECT DISTINCT group_name FROM movies WHERE group_name IS NOT NULL AND group_name <> '' ORDER BY group_name ASC"
        )
    return [r["group_name"] for r in rows]


@router.message(AdminSG.mov_group_browser)
async def mov_group_browser(msg: Message, state: FSMContext):
    text = msg.text or ""
    if text == "🔎 QIDIRISH":
        await state.set_state(AdminSG.mov_group_search)
        await msg.answer("Qidiruv matnini kiriting:", reply_markup=kb.reply_kb([]))
        return
    data = await state.get_data()
    groups = await _movie_groups(data.get("list_filter"))
    if text == "⬅️ ORQAGA":
        await state.update_data(list_page=data.get("list_page", 0) - 1)
        await _send_list(msg, state, groups, "Tanlang:")
        return
    if text == "➡️ KEYINGI":
        await state.update_data(list_page=data.get("list_page", 0) + 1)
        await _send_list(msg, state, groups, "Tanlang:")
        return
    if text in groups:
        cnt = await db.fetchval("SELECT COUNT(*) FROM movies WHERE group_name = $1", text)
        last = await db.get_last_code()
        await state.update_data(add_group=text, next_part=cnt + 1)
        await state.set_state(AdminSG.add_ext_mov_code)
        await msg.answer(
            f"✅ Guruh: <b>{utils.h(text)}</b>\n🔢 <b>Oxirgi band kod:</b> {last}\n"
            f"✅ <b>Tavsiya:</b> {last + 1}\n\nYangi qism uchun kod kiriting:",
            reply_markup=kb.reply_kb([]),
        )
    else:
        await msg.answer("Ro'yxatdan tanlang.")


@router.message(AdminSG.mov_group_search)
async def mov_group_search(msg: Message, state: FSMContext):
    await state.update_data(list_filter=msg.text, list_page=0)
    await state.set_state(AdminSG.mov_group_browser)
    groups = await _movie_groups(msg.text)
    await _send_list(msg, state, groups, f"Qidiruv natijalari ({utils.h(msg.text)}):")


@router.message(AdminSG.add_movie_name)
async def add_movie_name(msg: Message, state: FSMContext):
    name = utils.capitalize_name(msg.text or "")
    last = await db.get_last_code()
    await state.update_data(name=name)
    await state.set_state(AdminSG.add_movie_code)
    await msg.answer(
        f"📝 Nomi: <b>{utils.h(name)}</b> deb qabul qilindi.\n\n"
        f"🔢 <b>Oxirgi band kod:</b> {last}\n✅ <b>Tavsiya:</b> {last + 1}\n\nKino kodini kiriting:",
        reply_markup=kb.reply_kb([]),
    )


@router.message(AdminSG.add_movie_code)
async def add_movie_code(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text.isdigit() or await db.is_code_busy(int(text)):
        await msg.answer("⛔️ <b>Bu kod band yoki noto'g'ri!</b>\nBoshqa kod yozing:")
        return
    await state.update_data(code=int(text), parts=[])
    await state.set_state(AdminSG.add_movie_file)
    await msg.answer(
        "Endi kino videosini (yoki bir nechta qismlarni) yuboring.\nTugatgach <b>TUGATISH</b> ni bosing.",
        reply_markup=kb.reply_kb(["TUGATISH"]),
    )


@router.message(AdminSG.add_movie_file, F.text == "TUGATISH")
async def add_movie_finish(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    files = data.get("parts", [])
    if not files:
        await msg.answer("Video yubormadingiz!")
        return
    code = data["code"]
    name = data["name"]
    saved = []
    for i, f in enumerate(files):
        cur = code + i
        if await db.is_code_busy(cur):
            cur = await db.get_last_code() + 1
        final_name = f"{name} {i + 1}-qism" if len(files) > 1 else name
        await db.execute(
            "INSERT INTO movies (code, name, group_name, file_id, views) VALUES ($1,$2,$3,$4,0)",
            cur, final_name, name, f,
        )
        await post_to_channel(bot, msg.chat.id, f, await utils.format_caption(final_name, cur), config.ARCHIVE_CHANNEL)
        saved.append({"code": cur, "name": final_name, "file_id": f})
    await state.update_data(saved_for_channel=saved)
    await state.set_state(AdminSG.ask_post_channel_mov)
    await msg.answer(
        "✅ Kino saqlandi va Arxivga tashlandi!\n\n📣 <b>Endi Asosiy kanalga ham yuboraymi?</b>",
        reply_markup=kb.reply_kb(["XA", "YO'Q"]),
    )


@router.message(AdminSG.add_movie_file, F.content_type.in_({"video", "document"}))
async def add_movie_file(msg: Message, state: FSMContext):
    fid = msg.video.file_id if msg.video else msg.document.file_id
    data = await state.get_data()
    parts = data.get("parts", [])
    parts.append(fid)
    await state.update_data(parts=parts)
    await msg.answer(f"{len(parts)}-qism qabul qilindi.")


@router.message(AdminSG.ask_post_channel_mov, F.text.in_({"XA", "YO'Q"}))
async def ask_post_channel_mov(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "XA":
        data = await state.get_data()
        items = data.get("saved_for_channel", [])
        count = 0
        for it in items:
            if await post_to_channel(bot, msg.chat.id, it["file_id"], await utils.format_caption(it["name"], it["code"]), config.UPLOAD_CHANNEL):
                count += 1
        await msg.answer(f"✅ {count} ta fayl Asosiy kanalga yuborildi!", reply_markup=kb.admin_menu())
    else:
        await msg.answer("Ok, asosiy kanalga yuborilmadi.", reply_markup=kb.admin_menu())
    await state.set_state(AdminSG.panel)


@router.message(AdminSG.add_ext_mov_code)
async def add_ext_mov_code(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text.isdigit() or await db.is_code_busy(int(text)):
        await msg.answer("⛔️ Bu kod band yoki noto'g'ri!")
        return
    await state.update_data(code=int(text))
    await state.set_state(AdminSG.add_ext_mov_file)
    await msg.answer("Videoni yuboring:")


@router.message(AdminSG.add_ext_mov_file, F.content_type.in_({"video", "document"}))
async def add_ext_mov_file(msg: Message, state: FSMContext, bot: Bot):
    fid = msg.video.file_id if msg.video else msg.document.file_id
    data = await state.get_data()
    group = data["add_group"]
    name = f"{group} {data['next_part']}-qism"
    code = data["code"]
    await db.execute(
        "INSERT INTO movies (code, name, group_name, file_id, views) VALUES ($1,$2,$3,$4,0)",
        code, name, group, fid,
    )
    await post_to_channel(bot, msg.chat.id, fid, await utils.format_caption(name, code), config.ARCHIVE_CHANNEL)
    await state.update_data(saved_for_channel=[{"code": code, "name": name, "file_id": fid}])
    await state.set_state(AdminSG.ask_post_channel_mov)
    await msg.answer(
        "✅ Qo'shildi va Arxivlandi!\n\n📣 <b>Asosiy Kanalga ham yuboraymi?</b>",
        reply_markup=kb.reply_kb(["XA", "YO'Q"]),
    )


# ================================================================== SERIAL QO'SHISH
@router.message(AdminSG.series_add_type, F.text == "YANGI SERIAL")
async def new_series(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.add_series_name)
    await msg.answer("Nomi:", reply_markup=kb.reply_kb([]))


@router.message(AdminSG.series_add_type, F.text == "QISM QO'SHISH")
async def add_episode_browse(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.ser_browser_add)
    await state.update_data(list_filter=None, list_page=0)
    rows = await db.fetch("SELECT name FROM series ORDER BY name ASC")
    await _send_list(msg, state, [r["name"] for r in rows], "Qaysi serialga qo'shasiz?")


async def _series_names(filter_):
    if filter_:
        rows = await db.fetch("SELECT name FROM series WHERE name ILIKE $1 ORDER BY name ASC", f"%{filter_}%")
    else:
        rows = await db.fetch("SELECT name FROM series ORDER BY name ASC")
    return [r["name"] for r in rows]


@router.message(AdminSG.ser_browser_add)
async def ser_browser_add(msg: Message, state: FSMContext):
    text = msg.text or ""
    if text == "🔎 QIDIRISH":
        await state.set_state(AdminSG.ser_group_search)
        await msg.answer("Qidiruv matnini kiriting:", reply_markup=kb.reply_kb([]))
        return
    data = await state.get_data()
    sers = await _series_names(data.get("list_filter"))
    if text == "⬅️ ORQAGA":
        await state.update_data(list_page=data.get("list_page", 0) - 1)
        await _send_list(msg, state, sers, "Tanlang:")
        return
    if text == "➡️ KEYINGI":
        await state.update_data(list_page=data.get("list_page", 0) + 1)
        await _send_list(msg, state, sers, "Tanlang:")
        return
    if text in sers:
        s = await db.fetchrow("SELECT * FROM series WHERE name = $1", text)
        mx = await db.fetchval("SELECT COALESCE(MAX(episode_number),0) FROM episodes WHERE series_id=$1", s["id"])
        await state.update_data(sid=s["id"], s_code=s["code"], s_name=s["name"], last_ep=int(mx), posted_eps=[])
        await state.set_state(AdminSG.add_ext_series_file)
        await msg.answer(
            f"✅ Serial: <b>{utils.h(s['name'])}</b>\nQismni yuboring (Video/Fayl). TUGATISH ni bosing.",
            reply_markup=kb.reply_kb(["TUGATISH"]),
        )
    else:
        await msg.answer("Ro'yxatdan tanlang.")


@router.message(AdminSG.ser_group_search)
async def ser_group_search(msg: Message, state: FSMContext):
    await state.update_data(list_filter=msg.text, list_page=0)
    await state.set_state(AdminSG.ser_browser_add)
    sers = await _series_names(msg.text)
    await _send_list(msg, state, sers, f"Qidiruv natijalari ({utils.h(msg.text)}):")


@router.message(AdminSG.add_ext_series_file, F.text == "TUGATISH")
async def add_ext_series_finish(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.ask_post_channel_ser)
    await msg.answer("Saqlandi!\n\n📣 <b>Asosiy Kanalga ham yuboraymi?</b>", reply_markup=kb.reply_kb(["XA", "YO'Q"]))


@router.message(AdminSG.add_ext_series_file, F.content_type.in_({"video", "document"}))
async def add_ext_series_file(msg: Message, state: FSMContext, bot: Bot):
    fid = msg.video.file_id if msg.video else msg.document.file_id
    data = await state.get_data()
    ep = data["last_ep"] + 1
    await db.execute("INSERT INTO episodes (series_id, episode_number, file_id) VALUES ($1,$2,$3)", data["sid"], ep, fid)
    await post_to_channel(bot, msg.chat.id, fid, await utils.format_caption(data["s_name"], data["s_code"], ep), config.ARCHIVE_CHANNEL)
    posted = data.get("posted_eps", [])
    posted.append({"fid": fid, "ep": ep})
    await state.update_data(last_ep=ep, posted_eps=posted)
    await msg.answer(f"{ep}-qism saqlandi (va arxivlandi).")


@router.message(AdminSG.add_series_name)
async def add_series_name(msg: Message, state: FSMContext):
    name = utils.capitalize_name(msg.text or "")
    last = await db.get_last_code()
    await state.update_data(name=name)
    await state.set_state(AdminSG.add_series_code)
    await msg.answer(
        f"📝 Nomi: <b>{utils.h(name)}</b> deb qabul qilindi.\n\n"
        f"🔢 <b>Oxirgi band kod:</b> {last}\n✅ <b>Tavsiya:</b> {last + 1}\n\nSerial kodini kiriting:",
        reply_markup=kb.reply_kb([]),
    )


@router.message(AdminSG.add_series_code)
async def add_series_code(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text.isdigit() or await db.is_code_busy(int(text)):
        await msg.answer("⛔️ Bu kod band yoki noto'g'ri!")
        return
    await state.update_data(code=int(text), posted_eps=[])
    await state.set_state(AdminSG.add_series_ep)
    await msg.answer("Qismlarni tashlang (Video/Fayl)...", reply_markup=kb.reply_kb(["TUGATISH"]))


@router.message(AdminSG.add_series_ep, F.text == "TUGATISH")
async def add_series_ep_finish(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.ask_post_channel_ser)
    await msg.answer("Saqlandi!\n\n📣 <b>Asosiy Kanalga ham yuboraymi?</b>", reply_markup=kb.reply_kb(["XA", "YO'Q"]))


@router.message(AdminSG.add_series_ep, F.content_type.in_({"video", "document"}))
async def add_series_ep(msg: Message, state: FSMContext, bot: Bot):
    fid = msg.video.file_id if msg.video else msg.document.file_id
    data = await state.get_data()
    code = data["code"]
    name = data["name"]
    s = await db.fetchrow("SELECT id, code, name FROM series WHERE code = $1", code)
    if not s:
        sid = await db.fetchval("INSERT INTO series (code, name, views) VALUES ($1,$2,0) RETURNING id", code, name)
        s_name, s_code = name, code
    else:
        sid, s_name, s_code = s["id"], s["name"], s["code"]
    await state.update_data(sid=sid, s_name=s_name, s_code=s_code)
    cnt = await db.fetchval("SELECT COUNT(*) FROM episodes WHERE series_id = $1", sid)
    ep = int(cnt) + 1
    await db.execute("INSERT INTO episodes (series_id, episode_number, file_id) VALUES ($1,$2,$3)", sid, ep, fid)
    await post_to_channel(bot, msg.chat.id, fid, await utils.format_caption(name, code, ep), config.ARCHIVE_CHANNEL)
    posted = data.get("posted_eps", [])
    posted.append({"fid": fid, "ep": ep})
    await state.update_data(posted_eps=posted)
    await msg.answer(f"{ep}-qism (arxivlandi).")


@router.message(AdminSG.ask_post_channel_ser, F.text.in_({"XA", "YO'Q"}))
async def ask_post_channel_ser(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if msg.text == "XA":
        eps = data.get("posted_eps", [])
        s_name, s_code = data.get("s_name"), data.get("s_code")
        count = 0
        for e in eps:
            if await post_to_channel(bot, msg.chat.id, e["fid"], await utils.format_caption(s_name, s_code, e["ep"]), config.UPLOAD_CHANNEL):
                count += 1
        await msg.answer(f"✅ {count} ta qism Asosiy kanalga yuborildi!", reply_markup=kb.admin_menu())
    else:
        await msg.answer("Ok, asosiy kanalga yuborilmadi.", reply_markup=kb.admin_menu())
    await state.update_data(posted_eps=[])
    await state.set_state(AdminSG.panel)


# ================================================================== RENAME
async def _rename_browser(msg, state, table, next_state):
    text = msg.text or ""
    if text == "🔎 QIDIRISH":
        await state.set_state(AdminSG.rename_mov_search if table == "movies" else AdminSG.rename_ser_search)
        await msg.answer("Qidiruv matnini kiriting:", reply_markup=kb.reply_kb([]))
        return
    data = await state.get_data()
    filter_ = data.get("list_filter")
    if filter_:
        rows = await db.fetch(f"SELECT name FROM {table} WHERE name ILIKE $1 ORDER BY id DESC", f"%{filter_}%")
    else:
        limit = " LIMIT 500" if table == "movies" else ""
        rows = await db.fetch(f"SELECT name FROM {table} ORDER BY id DESC{limit}")
    items = [r["name"] for r in rows]
    if text == "⬅️ ORQAGA":
        await state.update_data(list_page=data.get("list_page", 0) - 1)
        await _send_list(msg, state, items, "Tanlang:")
        return
    if text == "➡️ KEYINGI":
        await state.update_data(list_page=data.get("list_page", 0) + 1)
        await _send_list(msg, state, items, "Tanlang:")
        return
    if text in items:
        await state.update_data(rename_target=text)
        await state.set_state(next_state)
        await msg.answer(f"Eski nom: <b>{utils.h(text)}</b>\n\nYangi nomni yozing:", reply_markup=kb.reply_kb(["BEKOR QILISH"]))
    else:
        await msg.answer("Ro'yxatdan tanlang.")


@router.message(AdminSG.mov_rename_browser)
async def mov_rename_browser(msg: Message, state: FSMContext):
    await _rename_browser(msg, state, "movies", AdminSG.mov_rename_input)


@router.message(AdminSG.ser_rename_browser)
async def ser_rename_browser(msg: Message, state: FSMContext):
    await _rename_browser(msg, state, "series", AdminSG.ser_rename_input)


@router.message(AdminSG.rename_mov_search)
async def rename_mov_search(msg: Message, state: FSMContext):
    await state.update_data(list_filter=msg.text, list_page=0)
    await state.set_state(AdminSG.mov_rename_browser)
    rows = await db.fetch("SELECT name FROM movies WHERE name ILIKE $1 ORDER BY id DESC", f"%{msg.text}%")
    await _send_list(msg, state, [r["name"] for r in rows], "Natijalar:")


@router.message(AdminSG.rename_ser_search)
async def rename_ser_search(msg: Message, state: FSMContext):
    await state.update_data(list_filter=msg.text, list_page=0)
    await state.set_state(AdminSG.ser_rename_browser)
    rows = await db.fetch("SELECT name FROM series WHERE name ILIKE $1 ORDER BY id DESC", f"%{msg.text}%")
    await _send_list(msg, state, [r["name"] for r in rows], "Natijalar:")


@router.message(AdminSG.mov_rename_input)
async def mov_rename_input(msg: Message, state: FSMContext):
    if msg.text == "BEKOR QILISH":
        await state.set_state(AdminSG.panel)
        await msg.answer("Bekor qilindi.", reply_markup=kb.admin_menu())
        return
    data = await state.get_data()
    old = data["rename_target"]
    new = utils.capitalize_name(msg.text or "")
    await db.execute("UPDATE movies SET name=$1 WHERE name=$2", new, old)
    await db.execute("UPDATE movies SET group_name=$1 WHERE group_name=$2", new, old)
    await state.set_state(AdminSG.panel)
    await msg.answer(f"✅ O'zgartirildi:\n{utils.h(old)} → <b>{utils.h(new)}</b>", reply_markup=kb.admin_menu())


@router.message(AdminSG.ser_rename_input)
async def ser_rename_input(msg: Message, state: FSMContext):
    if msg.text == "BEKOR QILISH":
        await state.set_state(AdminSG.panel)
        await msg.answer("Bekor qilindi.", reply_markup=kb.admin_menu())
        return
    data = await state.get_data()
    old = data["rename_target"]
    new = utils.capitalize_name(msg.text or "")
    await db.execute("UPDATE series SET name=$1 WHERE name=$2", new, old)
    await state.set_state(AdminSG.panel)
    await msg.answer(f"✅ O'zgartirildi:\n{utils.h(old)} → <b>{utils.h(new)}</b>", reply_markup=kb.admin_menu())


# ================================================================== DELETE
@router.message(AdminSG.del_choice, F.text == "KINO")
async def del_choice_mov(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.del_mov)
    rows = await db.fetch("SELECT name FROM movies ORDER BY id DESC LIMIT 30")
    await msg.answer("Tanlang (yoki nomini yozing):", reply_markup=kb.reply_kb([r["name"] for r in rows]))


@router.message(AdminSG.del_choice, F.text == "SERIAL")
async def del_choice_ser(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.del_ser)
    rows = await db.fetch("SELECT name FROM series ORDER BY id DESC LIMIT 30")
    await msg.answer("Tanlang (yoki nomini yozing):", reply_markup=kb.reply_kb([r["name"] for r in rows]))


@router.message(AdminSG.del_mov)
async def del_mov(msg: Message, state: FSMContext):
    await db.execute("DELETE FROM movies WHERE name=$1", msg.text)
    await state.set_state(AdminSG.panel)
    await msg.answer("O'chirildi.", reply_markup=kb.admin_menu())


@router.message(AdminSG.del_ser)
async def del_ser(msg: Message, state: FSMContext):
    await db.execute("DELETE FROM series WHERE name=$1", msg.text)
    await state.set_state(AdminSG.panel)
    await msg.answer("O'chirildi.", reply_markup=kb.admin_menu())


# ================================================================== MANBA
@router.message(AdminSG.set_sig)
async def set_sig(msg: Message, state: FSMContext):
    await db.execute("UPDATE settings SET signature=$1 WHERE id=1", msg.text)
    await state.set_state(AdminSG.panel)
    await msg.answer("Saqlandi!", reply_markup=kb.admin_menu())


# ================================================================== OBUNA
@router.message(AdminSG.sub_sets, F.text == "YOQISH")
async def sub_on(msg: Message):
    await db.execute("UPDATE settings SET force_sub_status=1 WHERE id=1")
    await msg.answer("Yoqildi.")


@router.message(AdminSG.sub_sets, F.text == "O'CHIRISH")
async def sub_off(msg: Message):
    await db.execute("UPDATE settings SET force_sub_status=0 WHERE id=1")
    await msg.answer("O'chirildi.")


@router.message(AdminSG.sub_sets, F.text == "KANAL QO'SHISH")
async def sub_add_ch(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.add_ch)
    await msg.answer("Kanal Usernameni (@kanal) yuboring:")


@router.message(AdminSG.sub_sets, F.text == "KANAL O'CHIRISH")
async def sub_del_ch(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.del_ch)
    rows = await db.fetch("SELECT title FROM channels")
    await msg.answer("Tanlang:", reply_markup=kb.reply_kb([r["title"] for r in rows]))


@router.message(AdminSG.add_ch)
async def add_ch(msg: Message, state: FSMContext, bot: Bot):
    import re
    text = (msg.text or "").strip()
    tid = text
    m = re.search(r"(?:t\.me/|telegram\.me/|@)([\w\-]+)", text)
    if m:
        tid = "@" + m.group(1)
    try:
        chat = await bot.get_chat(tid)
    except Exception:
        await msg.answer(
            "❌ Kanal topilmadi.\n1. Botni kanalga <b>ADMIN</b> qiling.\n2. Kanal username (@kanal) yoki ID sini yuboring."
        )
        return
    link = None
    if chat.username:
        link = f"https://t.me/{chat.username}"
    else:
        try:
            link = await bot.export_chat_invite_link(chat.id)
        except Exception:
            link = None
    if not link:
        await state.update_data(ch_id_wait=chat.id, ch_title_wait=chat.title)
        await state.set_state(AdminSG.add_ch_link)
        await msg.answer(
            f"⚠️ Kanal topildi, lekin havolani olib bo'lmadi.\nKanal ID: <code>{chat.id}</code>\n\n"
            "Iltimos, kanalning <b>Taklif havolasini</b> yuboring:"
        )
        return
    await db.execute("INSERT INTO channels (channel_id, title, link) VALUES ($1,$2,$3)", str(chat.id), chat.title, link)
    await state.set_state(AdminSG.panel)
    await msg.answer("✅ Kanal qo'shildi!", reply_markup=kb.admin_menu())


@router.message(AdminSG.add_ch_link)
async def add_ch_link(msg: Message, state: FSMContext):
    link = (msg.text or "").strip()
    if not link.startswith("http") and "t.me" in link:
        link = "https://" + link
    if not link.startswith("http"):
        await msg.answer("❌ Noto'g'ri havola. Qayta yuboring:")
        return
    data = await state.get_data()
    await db.execute("INSERT INTO channels (channel_id, title, link) VALUES ($1,$2,$3)", str(data["ch_id_wait"]), data["ch_title_wait"], link)
    await state.set_state(AdminSG.panel)
    await msg.answer("✅ Kanal va havola saqlandi!", reply_markup=kb.admin_menu())


@router.message(AdminSG.del_ch)
async def del_ch(msg: Message, state: FSMContext):
    await db.execute("DELETE FROM channels WHERE title=$1", msg.text)
    await state.set_state(AdminSG.panel)
    await msg.answer("O'chirildi.", reply_markup=kb.admin_menu())


# ================================================================== IJTIMOIY TARMOQLAR
@router.message(AdminSG.social_menu, F.text == "➕ QO'SHISH")
async def social_add_prompt(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.add_social)
    await msg.answer("Ijtimoiy tarmoq havolasini yuboring (Masalan: https://instagram.com/myprofile):", reply_markup=kb.reply_kb([]))


@router.message(AdminSG.social_menu, F.text == "📋 RO'YXAT")
async def social_list(msg: Message):
    rows = await db.fetch("SELECT platform, url FROM social_links")
    if not rows:
        await msg.answer("Hozircha ijtimoiy tarmoqlar yo‘q.")
        return
    out = "<b>Ijtimoiy tarmoqlar ro'yxati:</b>\n\n"
    for s in rows:
        out += f"🔹 <b>{utils.h(s['platform'])}</b> - {utils.h(s['url'])}\n"
    await msg.answer(out, disable_web_page_preview=True)


@router.message(AdminSG.social_menu, F.text == "🗑 O'CHIRISH")
async def social_del_prompt(msg: Message, state: FSMContext):
    rows = await db.fetch("SELECT platform FROM social_links")
    if not rows:
        await msg.answer("O'chirish uchun hech narsa yo'q.")
        return
    await state.set_state(AdminSG.del_social)
    await msg.answer("Tanlang:", reply_markup=kb.reply_kb([r["platform"] for r in rows]))


@router.message(AdminSG.add_social)
async def social_add(msg: Message, state: FSMContext):
    url = (msg.text or "").strip()
    if not url.startswith("http"):
        await msg.answer("❌ Noto'g'ri URL. Qaytadan yuboring:")
        return
    platform = _detect_platform(url)
    await db.execute("INSERT INTO social_links (platform, url) VALUES ($1,$2)", platform, url)
    await state.set_state(AdminSG.panel)
    await msg.answer(f"✅ <b>{utils.h(platform)}</b> muvaffaqiyatli qo'shildi!", reply_markup=kb.admin_menu())


@router.message(AdminSG.del_social)
async def social_del(msg: Message, state: FSMContext):
    await db.execute("DELETE FROM social_links WHERE platform=$1", msg.text)
    await state.set_state(AdminSG.panel)
    await msg.answer("✅ O'chirildi.", reply_markup=kb.admin_menu())


# ================================================================== REKLAMA (broadcast)
@router.message(AdminSG.broad_collect, F.text == "BEKOR QILISH")
async def broad_cancel(msg: Message, state: FSMContext):
    await state.set_state(AdminSG.panel)
    await msg.answer("Bekor qilindi.", reply_markup=kb.admin_menu())


@router.message(AdminSG.broad_collect, F.text == "BOSHLASH")
async def broad_start(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    raw = data.get("broad_list", [])
    if not raw:
        await msg.answer("Hech narsa yubormadingiz!")
        return
    await state.set_state(AdminSG.panel)
    await msg.answer("🚀 Tarqatish boshlandi! Yakunida hisobot keladi.", reply_markup=kb.admin_menu())
    asyncio.create_task(_run_broadcast(bot, msg.chat.id, msg.chat.id, raw))


@router.message(AdminSG.broad_collect)
async def broad_collect(msg: Message, state: FSMContext):
    data = await state.get_data()
    lst = data.get("broad_list", [])
    lst.append({"from_id": msg.chat.id, "msg_id": msg.message_id})
    await state.update_data(broad_list=lst)


async def _run_broadcast(bot: Bot, admin_id: int, from_id: int, tasks: list[dict]):
    rows = await db.fetch("SELECT chat_id FROM users WHERE is_active = TRUE")
    ok = fail = 0
    for r in rows:
        cid = r["chat_id"]
        delivered = True
        for t in tasks:
            try:
                await bot.copy_message(cid, t["from_id"], t["msg_id"])
            except Exception:
                delivered = False
        if delivered:
            ok += 1
        else:
            fail += 1
            await db.execute("UPDATE users SET is_active = FALSE WHERE chat_id = $1", cid)
        await asyncio.sleep(0.05)  # ~20 msg/s — Telegram limitiga rioya
    await bot.send_message(
        admin_id,
        f"✅ <b>Reklama tarqatish yakunlandi!</b>\n\n📬 Yetkazildi: <b>{ok}</b>\n🚫 Bloklagan/xato: <b>{fail}</b>",
    )
