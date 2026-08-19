"""
Quiz bot — Telegram test boti (aiogram 3.x + PostgreSQL).

Foydalanuvchi interfeysi:
  • Doimiy pastki menyu (Testlar / Sevimli / Reyting / Profilim / Yordam)
  • Kategoriyalar, qidiruv, sahifalash, sevimli va so'nggi o'ynalgan testlar
  • Rejim tanlash: 🎓 Mashq (vaqtsiz, izohli) yoki 📝 Imtihon (vaqtli)
  • Boshlash kartochkasi, progress bar, boyitilgan natija + xatolar tahlili
  • Natija kartochkasi (rasm), profil, streak, XP/daraja, nishonlar
  • Guruhda jonli tabel + tezlik + guruh reytingi
  • Interaktiv (bittalab) va matnli test yaratish, rasmli savollar
"""

from __future__ import annotations

import asyncio
import html
import logging
import random
import re
import time

from aiogram import Bot, Dispatcher, F
from aiogram.enums import PollType
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    PollAnswer,
    ReplyKeyboardMarkup,
)

import cards
import db
import game
from config import settings
from parser import parse_quiz

log = logging.getLogger("quizbot")

# Faol sessiyalar:  chat_id -> session dict
sessions: dict[int, dict] = {}
# poll_id -> chat_id
poll_map: dict[str, int] = {}
# user_id -> so'nggi noto'g'ri javoblar [{"q":q,"chosen":idx}]
last_wrong: dict[int, list] = {}
# user_id -> kutilayotgan kiritish (qidiruv / matn / interaktiv yaratish)
await_input: dict[int, dict] = {}
# user_id -> tasdiq kutayotgan tayyor test {"name","questions"}
pending_quiz: dict[int, dict] = {}

GROUP_DEFAULT_TIMER = 20
EXAM_DEFAULT_TIMER = 30
PAGE = 8  # ro'yxatda bir sahifadagi testlar

_OPT_MARK = re.compile(r"^\s*([A-Da-d][.)]|[+\-*]|#|\d+[.)])", re.M)

# ─── menyu tugmalari (matnlari) ───
BTN_TESTS = "📚 Testlar"
BTN_FAV = "⭐ Sevimli"
BTN_TOP = "🏆 Reyting"
BTN_PROFILE = "📊 Profilim"
BTN_HELP = "ℹ️ Yordam"
BTN_CREATE = "➕ Test yaratish"
MENU_TEXTS = {BTN_TESTS, BTN_FAV, BTN_TOP, BTN_PROFILE, BTN_HELP, BTN_CREATE}


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def share_link(quiz_id: int) -> str:
    return f"https://t.me/{settings.BOT_USERNAME}?start=test_{quiz_id}"


def is_admin(user_id: int) -> bool:
    return not settings.ADMIN_IDS or user_id in settings.ADMIN_IDS


async def can_create(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    return (await db.get_setting("user_create", "0")) == "1"


def main_menu_kb(user_id: int, is_creator: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_TESTS), KeyboardButton(text=BTN_FAV)],
        [KeyboardButton(text=BTN_TOP), KeyboardButton(text=BTN_PROFILE)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    if is_creator:
        rows[-1].append(KeyboardButton(text=BTN_CREATE))
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def _bg(coro) -> None:
    async def runner():
        try:
            await coro
        except Exception:
            log.exception("Fon vazifasi xato berdi")
    asyncio.create_task(runner())


async def _typing(bot: Bot, chat_id: int) -> None:
    try:
        await bot.send_chat_action(chat_id, "typing")
    except Exception:
        pass


async def _send_long(bot: Bot, chat_id: int, text: str, **kw) -> None:
    """4096 belgidan uzun matnni qatorlar bo'yicha bo'lib yuboradi."""
    if len(text) <= 3900:
        await bot.send_message(chat_id, text, **kw)
        return
    chunk = ""
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > 3900:
            await bot.send_message(chat_id, chunk, **kw)
            chunk = ""
        chunk += line + "\n"
    if chunk.strip():
        await bot.send_message(chat_id, chunk, **kw)


def limit_warnings(questions: list[dict]) -> str:
    long_q = sum(1 for q in questions if len(q["text"]) > settings.QUESTION_LIMIT)
    long_o = sum(1 for q in questions for o in q["options"]
                 if len(str(o)) > settings.OPTION_LIMIT)
    if not long_q and not long_o:
        return ""
    parts = []
    if long_q:
        parts.append(f"{long_q} ta savol matni")
    if long_o:
        parts.append(f"{long_o} ta variant")
    return f"\n⚠️ {' va '.join(parts)} juda uzun — Telegram'da qisqartirilib ko'rsatiladi."


WELCOME = (
    "👋 <b>Assalomu alaykum! Bu — Quiz (Test) bot.</b>\n\n"
    "Bilimingizni sinang, reytingda ko'tariling, xatolaringiz ustida ishlang!\n\n"
    "📚 <b>Testlar</b> — mavjud testlarni tanlab yeching\n"
    "🏆 <b>Reyting</b> — eng yaxshi natijalar\n"
    "📊 <b>Profilim</b> — daraja, streak, nishonlar\n"
    "⭐ <b>Sevimli</b> — belgilagan testlaringiz\n\n"
    "Pastdagi menyudan foydalaning 👇"
)

HELP = (
    "ℹ️ <b>Yordam</b>\n\n"
    "<b>Menyu tugmalari:</b>\n"
    "📚 Testlar — kategoriyalar, qidiruv, sevimlilar\n"
    "🏆 Reyting — umumiy va haftalik\n"
    "📊 Profilim — daraja, XP, streak, nishonlar\n\n"
    "<b>Rejimlar:</b>\n"
    "🎓 <b>Mashq</b> — vaqt cheklovsiz, har savoldan keyin izoh ko'rinadi\n"
    "📝 <b>Imtihon</b> — har savolga vaqt, izohlar oxirida\n\n"
    "👥 Meni <b>guruhga</b> qo'shsangiz, birga o'ynash mumkin.\n\n"
    "<b>Test yaratish</b> (ruxsat bo'lsa) — <b>.txt</b> fayl yoki matn yuboring:\n"
    "<b>1-format:</b>\n"
    "<pre>1. Savol matni\nA) Variant\nB) Variant\nJavob: A</pre>\n"
    "<b>2-format</b> (to'g'ri javob <b>+</b>, ixtiyoriy <b>Izoh:</b>):\n"
    "<pre># Savol matni\n+ To'g'ri variant\n- Variant\nIzoh: tushuntirish</pre>\n"
    "Yoki menyudan «➕ Test yaratish» → bittalab qo'shing.\n\n"
    "<b>Buyruqlar:</b> /testlar /reyting /profil /natijalarim /sevimli /stop"
)


# ═══════════════════════════ REGISTER ═══════════════════════════

def register(dp: Dispatcher, bot: Bot) -> None:

    # ─────────── xatolarni tutish ───────────
    @dp.error()
    async def on_error(event: ErrorEvent):
        log.exception("Handler xatosi", exc_info=event.exception)
        upd = event.update
        chat_id = None
        try:
            if upd.message:
                chat_id = upd.message.chat.id
            elif upd.callback_query and upd.callback_query.message:
                chat_id = upd.callback_query.message.chat.id
        except Exception:
            pass
        if chat_id:
            try:
                await bot.send_message(chat_id, "⚠️ Kutilmagan xatolik yuz berdi. Qaytadan urinib ko'ring.")
            except Exception:
                pass
        return True

    # ─────────── /start ───────────
    @dp.message(CommandStart())
    async def cmd_start(message: Message, command: CommandObject = None):
        u = message.from_user
        await db.ensure_user(u.id, u.username, u.first_name)
        await_input.pop(u.id, None)
        payload = (command.args if command else None) or ""
        if payload.startswith("test_"):
            try:
                qid = int(payload[5:])
            except ValueError:
                qid = 0
            if qid and await db.get_quiz(qid):
                await show_quiz_card(bot, message.chat, u, qid)
                return
        is_priv = message.chat.type == "private"
        kb = main_menu_kb(u.id, await can_create(u.id)) if is_priv else None
        await message.answer(WELCOME, reply_markup=kb)

    # ─────────── /yordam ───────────
    @dp.message(Command("yordam", "help"))
    async def cmd_help(message: Message):
        await_input.pop(message.from_user.id, None)
        await message.answer(HELP)

    # ─────────── /testlar ───────────
    @dp.message(Command("testlar", "list", "quizlar"))
    async def cmd_list(message: Message):
        await_input.pop(message.from_user.id, None)
        await _typing(bot, message.chat.id)
        text, kb = await categories_screen(message.from_user.id)
        await message.answer(text, reply_markup=kb)

    # ─────────── /sevimli ───────────
    @dp.message(Command("sevimli", "favorites"))
    async def cmd_fav(message: Message):
        await_input.pop(message.from_user.id, None)
        await send_favorites(bot, message.chat.id, message.from_user.id)

    # ─────────── /reyting ───────────
    @dp.message(Command("reyting", "top", "leaderboard"))
    async def cmd_top(message: Message):
        await_input.pop(message.from_user.id, None)
        text, kb = await leaderboard_screen("all")
        await message.answer(text, reply_markup=kb)

    # ─────────── /profil ───────────
    @dp.message(Command("profil", "profile", "menim"))
    async def cmd_profile(message: Message):
        await_input.pop(message.from_user.id, None)
        await send_profile(bot, message.chat.id, message.from_user)

    # ─────────── /natijalarim ───────────
    @dp.message(Command("natijalarim", "myresults", "mystats", "tarix"))
    async def cmd_myresults(message: Message):
        await_input.pop(message.from_user.id, None)
        await send_history(bot, message.chat.id, message.from_user.id)

    # ─────────── /yaratish ───────────
    @dp.message(Command("yaratish", "yarat", "create"))
    async def cmd_create(message: Message):
        await_input.pop(message.from_user.id, None)
        if not await can_create(message.from_user.id):
            await message.answer("⛔ Sizda test yaratish huquqi yo'q.")
            return
        ct, ckb = creation_menu()
        await message.answer(ct, reply_markup=ckb)

    # ─────────── /stop ───────────
    @dp.message(Command("stop", "toxtat"))
    async def cmd_stop(message: Message):
        await_input.pop(message.from_user.id, None)
        s = sessions.get(message.chat.id)
        if not s:
            await message.answer("Faol test yo'q.")
            return
        if s["mode"] == "group" and message.from_user.id != s["starter"] \
                and not is_admin(message.from_user.id):
            await message.answer("⛔ Faqat testni boshlagan yoki admin to'xtata oladi.")
            return
        _cleanup_session(message.chat.id)
        await message.answer("⏹ Test to'xtatildi.")

    # ─────────── /pauza va /davom ───────────
    @dp.message(Command("pauza", "pause"))
    async def cmd_pause(message: Message):
        s = sessions.get(message.chat.id)
        if not s or s["mode"] != "private":
            await message.answer("Pauza qilish uchun faol shaxsiy test yo'q.")
            return
        s["paused"] = True
        await message.answer("⏸ Keyingi savol pauzada. Davom etish: /davom")

    @dp.message(Command("davom", "resume"))
    async def cmd_resume(message: Message):
        await _resume(bot, message.chat.id)

    # ─────────── .txt fayl ───────────
    @dp.message(F.document)
    async def on_document(message: Message):
        u = message.from_user
        await db.ensure_user(u.id, u.username, u.first_name)
        if not await can_create(u.id):
            await message.answer("⛔ Sizda test yuklash huquqi yo'q.")
            return
        doc = message.document
        if not (doc.file_name or "").lower().endswith(".txt"):
            await message.answer("❗ Iltimos, <b>.txt</b> formatidagi fayl yuboring.")
            return
        buf = await bot.download(doc)
        text = buf.read().decode("utf-8-sig", errors="replace")
        questions = [q for q in parse_quiz(text) if len(q["options"]) >= 2]
        if not questions:
            await message.answer("❌ Fayldan biror savol topilmadi.\nFormatni tekshiring (ℹ️ Yordam).")
            return
        name = doc.file_name.rsplit(".", 1)[0]
        await preview_quiz(bot, message.chat.id, u.id, name, questions)

    # ─────────── rasm (interaktiv yaratishda rasmli savol) ───────────
    @dp.message(F.photo)
    async def on_photo(message: Message):
        u = message.from_user
        st = await_input.get(u.id)
        if st and st.get("kind") == "build" and st.get("step") == "q":
            file_id = message.photo[-1].file_id
            caption = (message.caption or "").strip()
            if not caption:
                await message.answer("🖼 Rasm qabul qilindi. Endi savol matnini yozing "
                                     "(rasm shu savolga biriktiriladi):")
                st["pending_image"] = file_id
                return
            st["cur"] = {"text": caption, "image_file_id": file_id}
            st["step"] = "opts"
            await message.answer("Endi <b>variantlarni</b> yuboring (har qatorda bittadan, "
                                 "to'g'risini <b>+</b> bilan belgilang):\n<pre>+ To'g'ri\n- Xato\n- Xato</pre>")
            return
        # aks holda e'tiborsiz

    # ─────────── matn (menyu / qidiruv / yaratish) ───────────
    @dp.message(F.text)
    async def on_text(message: Message):
        u = message.from_user
        text = message.text or ""
        await db.ensure_user(u.id, u.username, u.first_name)

        # 1) kutilayotgan kiritish
        st = await_input.get(u.id)
        if st and text not in MENU_TEXTS and not (text.startswith("/") and st.get("kind") != "build"):
            handled = await _handle_pending(bot, message, st)
            if handled:
                return
        elif st and (text in MENU_TEXTS or text.startswith("/")):
            await_input.pop(u.id, None)  # menyu bosildi — bekor qilamiz

        # 2) menyu tugmalari (faqat shaxsiy chat)
        if message.chat.type == "private":
            if text == BTN_TESTS:
                await _typing(bot, message.chat.id)
                t, kb = await categories_screen(u.id)
                await message.answer(t, reply_markup=kb)
                return
            if text == BTN_FAV:
                await send_favorites(bot, message.chat.id, u.id)
                return
            if text == BTN_TOP:
                t, kb = await leaderboard_screen("all")
                await message.answer(t, reply_markup=kb)
                return
            if text == BTN_PROFILE:
                await send_profile(bot, message.chat.id, u)
                return
            if text == BTN_HELP:
                await message.answer(HELP)
                return
            if text == BTN_CREATE:
                if await can_create(u.id):
                    ct, ckb = creation_menu()
                    await message.answer(ct, reply_markup=ckb)
                else:
                    await message.answer("⛔ Sizda test yaratish huquqi yo'q.")
                return

        # 3) noma'lum buyruq — jim
        if text.startswith("/"):
            return

        # 4) yaratuvchi bo'lsa: matnni test sifatida ko'rib chiqamiz
        if await can_create(u.id):
            questions = [q for q in parse_quiz(text) if len(q["options"]) >= 2]
            if questions:
                name = (questions[0]["text"][:40].strip() or "Matnli test")
                await preview_quiz(bot, message.chat.id, u.id, name, questions)
                return
            if "\n" in text and _OPT_MARK.search(text):
                await message.answer("❌ Savol topilmadi. Formatni tekshiring — ℹ️ Yordam.")

    # ═══════════════════════ CALLBACKLAR ═══════════════════════

    async def _ans(cq: CallbackQuery):
        try:
            await cq.answer()
        except Exception:
            pass

    # kategoriyalar / ro'yxat
    @dp.callback_query(F.data == "cats")
    async def cb_cats(cq: CallbackQuery):
        await _ans(cq)
        t, kb = await categories_screen(cq.from_user.id)
        try:
            await cq.message.edit_text(t, reply_markup=kb)
        except Exception:
            await cq.message.answer(t, reply_markup=kb)

    @dp.callback_query(F.data.startswith("cat:"))
    async def cb_cat(cq: CallbackQuery):
        await _ans(cq)
        _, cat, page = cq.data.split(":")
        t, kb = await list_screen(cat, int(page))
        try:
            await cq.message.edit_text(t, reply_markup=kb)
        except Exception:
            await cq.message.answer(t, reply_markup=kb)

    @dp.callback_query(F.data.startswith("srch:"))
    async def cb_search(cq: CallbackQuery):
        await _ans(cq)
        cat = cq.data.split(":", 1)[1]
        await_input[cq.from_user.id] = {"kind": "search", "cat": cat}
        await cq.message.answer("🔍 Qidiriladigan test nomini yozing:")

    @dp.callback_query(F.data == "fav_list")
    async def cb_fav_list(cq: CallbackQuery):
        await _ans(cq)
        await send_favorites(bot, cq.message.chat.id, cq.from_user.id)

    # test kartochkasi
    @dp.callback_query(F.data.startswith("pick:"))
    async def cb_pick(cq: CallbackQuery):
        await _ans(cq)
        quiz_id = int(cq.data.split(":", 1)[1])
        await show_quiz_card(bot, cq.message.chat, cq.from_user, quiz_id)

    @dp.callback_query(F.data.startswith("fav:"))
    async def cb_fav(cq: CallbackQuery):
        quiz_id = int(cq.data.split(":", 1)[1])
        if await db.is_favorite(cq.from_user.id, quiz_id):
            await db.remove_favorite(cq.from_user.id, quiz_id)
            await cq.answer("☆ Sevimlilardan olib tashlandi")
        else:
            await db.add_favorite(cq.from_user.id, quiz_id)
            await cq.answer("⭐ Sevimlilarga qo'shildi")
        text, kb = await quiz_card_content(cq.from_user, quiz_id)
        if text:
            try:
                await cq.message.edit_text(text, reply_markup=kb)
            except Exception:
                pass

    @dp.callback_query(F.data.startswith("share:"))
    async def cb_share(cq: CallbackQuery):
        await _ans(cq)
        quiz_id = int(cq.data.split(":", 1)[1])
        quiz = await db.get_quiz(quiz_id)
        if quiz:
            await cq.message.answer(
                f"🔗 <b>{_esc(quiz['name'])}</b> testini ulashing:\n{share_link(quiz_id)}")

    @dp.callback_query(F.data.startswith("mode:"))
    async def cb_mode(cq: CallbackQuery):
        await _ans(cq)
        _, quiz_id, mode = cq.data.split(":")
        quiz_id = int(quiz_id)
        total = await db.count_questions(quiz_id)
        if total == 0:
            await cq.message.answer("Bu testda savol yo'q 😕")
            return
        if total <= 10:
            await begin_quiz(bot, cq.message.chat, cq.from_user, quiz_id, total, mode=mode)
            return
        buttons = []
        for n in (10, 20, 30, 50):
            if n < total:
                buttons.append(InlineKeyboardButton(text=f"{n} ta", callback_data=f"go:{quiz_id}:{mode}:{n}"))
        buttons.append(InlineKeyboardButton(text=f"Hammasi ({total})", callback_data=f"go:{quiz_id}:{mode}:0"))
        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        label = "🎓 Mashq" if mode == "practice" else "📝 Imtihon"
        await cq.message.answer(f"{label} · ❓ Nechta savol yechamiz?",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

    @dp.callback_query(F.data.startswith("go:"))
    async def cb_go(cq: CallbackQuery):
        await _ans(cq)
        _, quiz_id, mode, count = cq.data.split(":")
        await begin_quiz(bot, cq.message.chat, cq.from_user, int(quiz_id), int(count), mode=mode)

    @dp.callback_query(F.data == "retry")
    async def cb_retry(cq: CallbackQuery):
        await _ans(cq)
        await begin_quiz(bot, cq.message.chat, cq.from_user, 0, 0, mode="practice", retry=True)

    @dp.callback_query(F.data == "resume")
    async def cb_resume(cq: CallbackQuery):
        await _ans(cq)
        await _resume(bot, cq.message.chat.id)

    @dp.callback_query(F.data == "menu:list")
    async def cb_menu_list(cq: CallbackQuery):
        await _ans(cq)
        t, kb = await categories_screen(cq.from_user.id)
        await cq.message.answer(t, reply_markup=kb)

    # reyting
    @dp.callback_query(F.data.startswith("top:"))
    async def cb_top(cq: CallbackQuery):
        await _ans(cq)
        period = cq.data.split(":", 1)[1]
        t, kb = await leaderboard_screen(period)
        try:
            await cq.message.edit_text(t, reply_markup=kb)
        except Exception:
            await cq.message.answer(t, reply_markup=kb)

    @dp.callback_query(F.data.startswith("rank:"))
    async def cb_rank(cq: CallbackQuery):
        await _ans(cq)
        parts = cq.data.split(":")
        quiz_id = int(parts[1])
        period = parts[2] if len(parts) > 2 else "all"
        t, kb = await quiz_leaderboard_screen(quiz_id, period)
        try:
            await cq.message.edit_text(t, reply_markup=kb)
        except Exception:
            await cq.message.answer(t, reply_markup=kb)

    # profil
    @dp.callback_query(F.data == "prof")
    async def cb_prof(cq: CallbackQuery):
        await _ans(cq)
        await send_profile(bot, cq.message.chat.id, cq.from_user)

    @dp.callback_query(F.data == "hist")
    async def cb_hist(cq: CallbackQuery):
        await _ans(cq)
        await send_history(bot, cq.message.chat.id, cq.from_user.id)

    @dp.callback_query(F.data == "ach")
    async def cb_ach(cq: CallbackQuery):
        await _ans(cq)
        await send_achievements(bot, cq.message.chat.id, cq.from_user.id)

    # test yaratish
    @dp.callback_query(F.data.startswith("newq:"))
    async def cb_newq(cq: CallbackQuery):
        await _ans(cq)
        if not await can_create(cq.from_user.id):
            return
        kind = cq.data.split(":", 1)[1]
        if kind == "text":
            await_input[cq.from_user.id] = {"kind": "paste"}
            await cq.message.answer(
                "📋 Test matnini (yoki .txt faylni) yuboring. Format uchun — ℹ️ Yordam.")
        else:
            await_input[cq.from_user.id] = {"kind": "build", "step": "name",
                                            "name": "", "questions": [], "cur": {}}
            await cq.message.answer(
                "🧩 <b>Interaktiv yaratish.</b>\nAvval <b>test nomini</b> yozing "
                "(bekor qilish: /bekor):")

    @dp.callback_query(F.data == "qsave")
    async def cb_qsave(cq: CallbackQuery):
        await _ans(cq)
        pend = pending_quiz.pop(cq.from_user.id, None)
        if not pend:
            await cq.message.answer("⏳ Saqlanadigan test topilmadi (eskirgan).")
            return
        qid = await db.create_quiz(pend["name"], cq.from_user.id, pend["questions"])
        try:
            await cq.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await cq.message.answer(
            f"✅ <b>{_esc(pend['name'])}</b> saqlandi ({len(pend['questions'])} savol).\n"
            f"🔗 {share_link(qid)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="▶️ Boshlash", callback_data=f"pick:{qid}")]]))

    @dp.callback_query(F.data == "qcancel")
    async def cb_qcancel(cq: CallbackQuery):
        await _ans(cq)
        pending_quiz.pop(cq.from_user.id, None)
        try:
            await cq.message.edit_text("❌ Bekor qilindi.")
        except Exception:
            pass

    @dp.callback_query(F.data == "bdone")
    async def cb_bdone(cq: CallbackQuery):
        await _ans(cq)
        await _builder_finish(bot, cq.message.chat.id, cq.from_user.id)

    @dp.callback_query(F.data == "bcancel")
    async def cb_bcancel(cq: CallbackQuery):
        await _ans(cq)
        await_input.pop(cq.from_user.id, None)
        await cq.message.answer("❌ Yaratish bekor qilindi.")

    # ─────────── poll javobi ───────────
    @dp.poll_answer()
    async def on_poll_answer(poll_answer: PollAnswer):
        key = poll_map.get(poll_answer.poll_id)
        if key is None:
            return
        s = sessions.get(key)
        if not s or s.get("current_poll") != poll_answer.poll_id:
            return
        uid = poll_answer.user.id
        if uid in s["answered"]:
            return
        s["answered"].add(uid)
        uname = poll_answer.user.username
        # guruhda ko'pincha DM'da botni ishga tushirmagan a'zolar javob beradi —
        # ular users jadvaliga yozilmasa keyinroq add_xp/streak jimgina hech narsa qilmaydi
        await db.ensure_user(uid, uname, poll_answer.user.first_name)
        s["names"][uid] = (uname and f"@{uname}") or poll_answer.user.first_name or f"ID {uid}"
        q = s["questions"][s["index"]]
        chosen = poll_answer.option_ids[0] if poll_answer.option_ids else -1
        correct = chosen == q["correct"]
        if correct:
            s["scores"][uid] = s["scores"].get(uid, 0) + 1
            s["round"]["correct"].append(uid)
            # tezlik: shu savolda birinchi to'g'ri javob
            if s["mode"] == "group":
                elapsed = time.monotonic() - s.get("q_start", time.monotonic())
                s["speed"][uid] = s["speed"].get(uid, 0.0) + elapsed
                if s.get("first_correct") is None:
                    s["first_correct"] = uid
        else:
            s["scores"].setdefault(uid, 0)
            s["round"]["wrong"].append(uid)
            s["wrong"].setdefault(uid, []).append({"q": q, "chosen": chosen})
        _bg(db.log_answer(q.get("id"), s["quiz_id"], q["text"][:300],
                          uid, uname, chosen, correct))
        if s["mode"] == "private":
            await advance(bot, key)


# ─────────────────────────── ekranlar ───────────────────────────

async def categories_screen(user_id: int):
    cats = await db.list_categories()
    fav = await db.list_favorites(user_id, limit=1)
    recent = await db.recent_quizzes(user_id, limit=1)
    total_q = await db.count_quizzes(active_only=True)
    text = "📚 <b>Testlar</b>\nBo'lim tanlang yoki qidiring."
    rows = []
    top = [InlineKeyboardButton(text="🔍 Qidirish", callback_data="srch:all")]
    if fav:
        top.append(InlineKeyboardButton(text="⭐ Sevimlilar", callback_data="fav_list"))
    rows.append(top)
    if recent:
        r = recent[0]
        rows.append([InlineKeyboardButton(
            text=f"🕘 Davom: {r['name'][:28]}", callback_data=f"pick:{r['id']}")])
    for c in cats:
        if not c["q_count"]:
            continue
        rows.append([InlineKeyboardButton(
            text=f"{c['emoji']} {c['name']} ({c['q_count']})",
            callback_data=f"cat:{c['id']}:0")])
    unc = await db.uncategorized_count(active_only=True)
    if unc and cats:
        rows.append([InlineKeyboardButton(text=f"📁 Boshqalar ({unc})", callback_data="cat:none:0")])
    rows.append([InlineKeyboardButton(text=f"🗂 Barcha testlar ({total_q})", callback_data="cat:all:0")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def _quiz_row_label(q: dict) -> str:
    diff = game.difficulty_label(q.get("difficulty"))
    tail = f" · {diff}" if diff else ""
    return f"📝 {q['name']} ({q['q_count']}){tail}"


async def list_screen(cat: str, page: int, search: str = ""):
    if cat == "all":
        category_id = "__all__"
        title = "🗂 Barcha testlar"
    elif cat == "none":
        category_id = None
        title = "📁 Boshqalar"
    else:
        category_id = int(cat)
        c = await db.get_category(category_id)
        title = f"{c['emoji']} {c['name']}" if c else "Kategoriya"
    total = await db.count_quizzes(active_only=True, search=search, category_id=category_id)
    offset = page * PAGE
    quizzes = await db.list_quizzes(active_only=True, search=search,
                                    category_id=category_id, limit=PAGE, offset=offset)
    if search:
        title += f" · 🔍 «{search}»"
    if not quizzes:
        text = f"{title}\n\n📭 Hech narsa topilmadi."
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bo'limlar", callback_data="cats")]])
        return text, kb
    pages = max(1, (total + PAGE - 1) // PAGE)
    text = f"{title}\n<i>{total} ta test · {page+1}/{pages}-sahifa</i>"
    rows = [[InlineKeyboardButton(text=_quiz_row_label(q)[:60], callback_data=f"pick:{q['id']}")]
            for q in quizzes]
    nav = []
    catkey = cat
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"cat:{catkey}:{page-1}"))
    nav.append(InlineKeyboardButton(text="🔙 Bo'limlar", callback_data="cats"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"cat:{catkey}:{page+1}"))
    rows.append(nav)
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


async def send_favorites(bot: Bot, chat_id: int, user_id: int):
    favs = await db.list_favorites(user_id, limit=50)
    if not favs:
        await bot.send_message(chat_id, "⭐ Sevimli testlaringiz yo'q.\n"
                                        "Test kartochkasidagi ⭐ tugma orqali qo'shing.")
        return
    rows = [[InlineKeyboardButton(text=f"⭐ {q['name'][:40]} ({q['q_count']})",
                                  callback_data=f"pick:{q['id']}")] for q in favs]
    await bot.send_message(chat_id, "⭐ <b>Sevimli testlar:</b>",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


async def quiz_card_content(user, quiz_id: int):
    quiz = await db.get_quiz(quiz_id)
    if not quiz:
        return None, None
    total = await db.count_questions(quiz_id)
    stats = await db.quiz_attempt_stats(quiz_id)
    diff = quiz["difficulty"]
    if not diff:
        diff = game.difficulty_from_accuracy(await db.quiz_accuracy(quiz_id))
    fav = await db.is_favorite(user.id, quiz_id)
    avg = stats.get("avg_pct")
    cat = ""
    if quiz.get("category_name"):
        cat = f"{quiz.get('category_emoji') or '📁'} {quiz['category_name']}\n"
    lines = [f"📝 <b>{_esc(quiz['name'])}</b>", cat.strip()]
    meta = [f"❓ {total} savol", game.difficulty_label(diff)]
    if stats.get("attempts"):
        meta.append(f"👥 {stats['attempts']} urinish")
    if avg is not None:
        meta.append(f"⌀ {round(avg*100)}%")
    lines.append(" · ".join(m for m in meta if m))
    if quiz.get("description"):
        lines.append(f"\n{_esc(quiz['description'])}")
    lines.append("\nRejimni tanlang:")
    text = "\n".join(x for x in lines if x)
    fav_btn = ("☆ Sevimlidan olish" if fav else "⭐ Sevimli")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Mashq", callback_data=f"mode:{quiz_id}:practice"),
         InlineKeyboardButton(text="📝 Imtihon", callback_data=f"mode:{quiz_id}:exam")],
        [InlineKeyboardButton(text=fav_btn, callback_data=f"fav:{quiz_id}"),
         InlineKeyboardButton(text="🔗 Ulashish", callback_data=f"share:{quiz_id}")],
        [InlineKeyboardButton(text="🏆 Reyting", callback_data=f"rank:{quiz_id}:all"),
         InlineKeyboardButton(text="🔙 Testlar", callback_data="cats")],
    ])
    return text, kb


async def show_quiz_card(bot: Bot, chat, user, quiz_id: int):
    if sessions.get(chat.id):
        await bot.send_message(chat.id, "⏳ Bu yerda test allaqachon ketyapti. Avval /stop qiling.")
        return
    text, kb = await quiz_card_content(user, quiz_id)
    if not text:
        await bot.send_message(chat.id, "Test topilmadi 😕")
        return
    await bot.send_message(chat.id, text, reply_markup=kb)


async def leaderboard_screen(period: str):
    rows = await db.leaderboard(limit=15, period=period)
    title = "🏆 <b>Reyting — haftalik</b>" if period == "week" else "🏆 <b>Reyting — umumiy</b>"
    if not rows:
        text = title + "\n\nHali natija yo'q."
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = [title, "<i>O'rtacha natija bo'yicha</i>\n"]
        for i, r in enumerate(rows):
            m = medals[i] if i < 3 else f"{i+1}."
            name = r["username"] and f"@{r['username']}" or f"ID {r['user_id']}"
            pct = round((r["best"] or 0) * 100)
            lines.append(f"{m} {_esc(name)} — <b>{pct}%</b> ({r['tries']})")
        text = "\n".join(lines)
    other = "all" if period == "week" else "week"
    other_label = "📅 Umumiy" if period == "week" else "📅 Haftalik"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=other_label, callback_data=f"top:{other}"),
        InlineKeyboardButton(text="📊 Profilim", callback_data="prof")]])
    return text, kb


async def quiz_leaderboard_screen(quiz_id: int, period: str):
    rows = await db.leaderboard(quiz_id=quiz_id, limit=15, period=period)
    quiz = await db.get_quiz(quiz_id)
    qname = _esc(quiz["name"]) if quiz else "Test"
    head = f"🏆 <b>{qname}</b> — " + ("haftalik" if period == "week" else "umumiy")
    if not rows:
        text = head + "\n\nBu test bo'yicha hali natija yo'q."
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = [head + "\n"]
        for i, r in enumerate(rows):
            m = medals[i] if i < 3 else f"{i+1}."
            name = r["username"] and f"@{r['username']}" or f"ID {r['user_id']}"
            pct = round((r["best"] or 0) * 100)
            lines.append(f"{m} {_esc(name)} — <b>{pct}%</b>")
        text = "\n".join(lines)
    other = "all" if period == "week" else "week"
    other_label = "📅 Umumiy" if period == "week" else "📅 Haftalik"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=other_label, callback_data=f"rank:{quiz_id}:{other}"),
        InlineKeyboardButton(text="🔙 Testlar", callback_data="cats")]])
    return text, kb


# ─────────────────────────── profil / tarix / nishonlar ───────────────────────────

def _xp_bar(progress: float, width: int = 10) -> str:
    filled = max(0, min(width, round(progress * width)))
    return "▰" * filled + "▱" * (width - filled)


async def send_profile(bot: Bot, chat_id: int, user):
    await db.ensure_user(user.id, user.username, user.first_name)
    p = await db.user_profile(user.id)
    lvl = game.level_for_xp(p.get("xp", 0))
    ach_codes = await db.user_achievement_codes(user.id)
    name = user.username and f"@{user.username}" or (user.first_name or "Foydalanuvchi")
    attempts = p.get("attempts") or 0
    avg = p.get("avg_pct")
    best = p.get("best_pct")
    lines = [
        f"📊 <b>{_esc(name)}</b>",
        f"{lvl['title']} · <b>{lvl['level']}-daraja</b>",
        f"{_xp_bar(lvl['progress'])} {lvl['into']}/{lvl['need']} XP",
        "",
        f"🔥 Streak: <b>{p.get('streak', 0)}</b> kun (rekord {p.get('best_streak', 0)})",
        f"🎮 Yechilgan testlar: <b>{attempts}</b>",
        f"⌀ O'rtacha: <b>{round(avg*100) if avg is not None else 0}%</b>"
        + (f" · 🏅 Eng yaxshi: {round(best*100)}%" if best is not None else ""),
        f"💯 Benuqson (100%): <b>{p.get('perfect', 0)}</b> marta",
        f"🏆 Reytingdagi o'rin: <b>{p.get('rank') if attempts else '—'}</b>",
        f"🎖 Nishonlar: <b>{len(ach_codes)}/{len(game.ACHIEVEMENTS)}</b>",
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Tarix", callback_data="hist"),
         InlineKeyboardButton(text="🎖 Nishonlar", callback_data="ach")],
        [InlineKeyboardButton(text="🏆 Reyting", callback_data="top:all"),
         InlineKeyboardButton(text="📚 Testlar", callback_data="cats")],
    ])
    await bot.send_message(chat_id, "\n".join(lines), reply_markup=kb)


def _spark(pcts: list[int]) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    if not pcts:
        return ""
    return "".join(blocks[min(7, max(0, p * 8 // 100))] for p in pcts)


async def send_history(bot: Bot, chat_id: int, user_id: int):
    rows = await db.user_history(user_id, limit=12)
    if not rows:
        await bot.send_message(chat_id, "📊 Sizda hali natija yo'q. 📚 Testlar orqali boshlang.")
        return
    pcts = [round(r["score"] / r["total"] * 100) if r["total"] else 0 for r in rows]
    spark = _spark(list(reversed(pcts)))
    lines = ["📈 <b>So'nggi natijalaringiz:</b>"]
    if spark:
        lines.append(f"<code>{spark}</code>  (eskidan → yangiga)\n")
    for r in rows:
        pct = round(r["score"] / r["total"] * 100) if r["total"] else 0
        d = r["created_at"].strftime("%d.%m %H:%M")
        m = "🎓" if r.get("mode") == "practice" else ("📝" if r.get("mode") == "exam" else "•")
        lines.append(f"{m} {_esc(r['quiz_name'])} — <b>{r['score']}/{r['total']}</b> ({pct}%) · {d}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📊 Profilim", callback_data="prof")]])
    await bot.send_message(chat_id, "\n".join(lines), reply_markup=kb)


async def send_achievements(bot: Bot, chat_id: int, user_id: int):
    earned = await db.user_achievement_codes(user_id)
    lines = [f"🎖 <b>Nishonlar</b> ({len(earned)}/{len(game.ACHIEVEMENTS)})\n"]
    for code, (emoji, title, desc) in game.ACHIEVEMENTS.items():
        if code in earned:
            lines.append(f"{emoji} <b>{title}</b> — {desc}")
        else:
            lines.append(f"🔒 <s>{title}</s> — <i>{desc}</i>")
    await bot.send_message(chat_id, "\n".join(lines))


# ─────────────────────────── test yaratish ───────────────────────────

def creation_menu():
    text = ("➕ <b>Test yaratish</b>\nUsulni tanlang:")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Matn/fayl joylash", callback_data="newq:text")],
        [InlineKeyboardButton(text="🧩 Bittalab (interaktiv)", callback_data="newq:build")],
    ])
    return text, kb


async def preview_quiz(bot: Bot, chat_id: int, user_id: int, name: str, questions: list[dict]):
    """Tayyor testni saqlashdan oldin oldindan ko'rsatadi."""
    pending_quiz[user_id] = {"name": name, "questions": questions}
    warn = limit_warnings(questions)
    q0 = questions[0]
    sample_opts = "\n".join(
        f"{'✅' if j == q0['correct'] else '▫️'} {_esc(o)}" for j, o in enumerate(q0["options"]))
    text = (
        f"👀 <b>Oldindan ko'rish</b>\n\n"
        f"📝 Nomi: <b>{_esc(name)}</b>\n"
        f"📊 Topildi: <b>{len(questions)}</b> ta savol{warn}\n\n"
        f"<b>1-savol namunasi:</b>\n{_esc(q0['text'])}\n{sample_opts}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Saqlash", callback_data="qsave"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="qcancel")]])
    await bot.send_message(chat_id, text, reply_markup=kb)


async def _handle_pending(bot: Bot, message: Message, st: dict) -> bool:
    """await_input holatidagi matnni qayta ishlaydi. True = qayta ishlandi."""
    u = message.from_user
    text = (message.text or "").strip()
    kind = st.get("kind")

    if text.lower() in ("/bekor", "bekor"):
        await_input.pop(u.id, None)
        await message.answer("❌ Bekor qilindi.")
        return True

    if kind == "search":
        await_input.pop(u.id, None)
        t, kb = await list_screen(st.get("cat", "all"), 0, search=text[:60])
        await message.answer(t, reply_markup=kb)
        return True

    if kind == "paste":
        await_input.pop(u.id, None)
        questions = [q for q in parse_quiz(message.text or "") if len(q["options"]) >= 2]
        if not questions:
            await message.answer("❌ Savol topilmadi. Formatni tekshiring — ℹ️ Yordam.")
            return True
        name = (questions[0]["text"][:40].strip() or "Matnli test")
        await preview_quiz(bot, message.chat.id, u.id, name, questions)
        return True

    if kind == "build":
        return await _builder_step(bot, message, st)

    return False


async def _builder_step(bot: Bot, message: Message, st: dict) -> bool:
    u = message.from_user
    text = (message.text or "").strip()
    step = st.get("step")

    if step == "name":
        st["name"] = text[:100] or "Yangi test"
        st["step"] = "q"
        await message.answer(
            f"✅ Nomi: <b>{_esc(st['name'])}</b>\n\n"
            "Endi <b>1-savol matnini</b> yozing (yoki rasm yuboring). "
            "Tugatish uchun — /tugat")
        return True

    if step == "q":
        if text.lower() in ("/tugat", "tugat"):
            await _builder_finish(bot, message.chat.id, u.id)
            return True
        cur = {"text": text}
        if st.get("pending_image"):
            cur["image_file_id"] = st.pop("pending_image")
        st["cur"] = cur
        st["step"] = "opts"
        await message.answer(
            "Endi <b>variantlarni</b> yuboring (har qatorda bittadan), "
            "to'g'risini <b>+</b> bilan belgilang:\n<pre>+ To'g'ri javob\n- Xato\n- Xato</pre>\n"
            "Ixtiyoriy izoh: <code>Izoh: ...</code>")
        return True

    if step == "opts":
        opts = []
        correct = 0
        expl = None
        for ln in (message.text or "").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            low = ln.lower()
            if low.startswith("izoh:") or low.startswith("izoh -"):
                expl = ln.split(":", 1)[-1].strip() if ":" in ln else ln[5:].strip()
                continue
            if ln[0] in "+*":
                correct = len(opts)
                opts.append(ln[1:].strip())
            elif ln[0] == "-":
                opts.append(ln[1:].strip())
            else:
                opts.append(ln)
        opts = [o for o in opts if o]
        if len(opts) < 2:
            await message.answer("❗ Kamida 2 ta variant kerak. Qaytadan yuboring.")
            return True
        cur = st["cur"]
        cur.update({"options": opts, "correct": correct, "explanation": expl})
        st["questions"].append(cur)
        st["cur"] = {}
        st["step"] = "q"
        n = len(st["questions"])
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"✅ Tugatish ({n})", callback_data="bdone"),
            InlineKeyboardButton(text="❌ Bekor", callback_data="bcancel")]])
        await message.answer(
            f"➕ Savol qo'shildi ({n} ta). <b>Keyingi savol</b> matnini yozing "
            "yoki tugating:", reply_markup=kb)
        return True

    return False


async def _builder_finish(bot: Bot, chat_id: int, user_id: int):
    st = await_input.get(user_id)
    if not st or st.get("kind") != "build":
        return
    questions = st.get("questions", [])
    await_input.pop(user_id, None)
    if not questions:
        await bot.send_message(chat_id, "❌ Savol qo'shilmadi — bekor qilindi.")
        return
    name = st.get("name") or "Yangi test"
    qid = await db.create_quiz(name, user_id, questions)
    await bot.send_message(
        chat_id,
        f"✅ <b>{_esc(name)}</b> saqlandi ({len(questions)} savol).\n🔗 {share_link(qid)}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="▶️ Boshlash", callback_data=f"pick:{qid}")]]))


# ─────────────────────────── o'yin mantiq ───────────────────────────

def _cleanup_session(key: int):
    s = sessions.pop(key, None)
    if s:
        task = s.get("timer_task")
        if task:
            task.cancel()
        pid = s.get("current_poll")
        if pid:
            poll_map.pop(pid, None)
    return s


def _prepare(questions: list[dict], count: int, shuffle: bool) -> list[dict]:
    qs = list(questions)
    if shuffle:
        random.shuffle(qs)
    if count and count > 0:
        qs = qs[:count]
    out = []
    for q in qs:
        opts = list(q["options"])
        correct = q["correct"]
        if shuffle and len(opts) > 1:
            order = list(range(len(opts)))
            random.shuffle(order)
            opts = [q["options"][i] for i in order]
            correct = order.index(q["correct"]) if 0 <= q["correct"] < len(q["options"]) else 0
        out.append({"id": q.get("id"), "text": q["text"], "options": opts, "correct": correct,
                    "explanation": q.get("explanation"), "image_file_id": q.get("image_file_id")})
    return out


async def _game_settings() -> tuple[bool, int]:
    shuffle = (await db.get_setting("shuffle", "1" if settings.DEFAULT_SHUFFLE else "0")) == "1"
    try:
        timer = int(await db.get_setting("timer", str(settings.DEFAULT_QUESTION_TIME)))
    except ValueError:
        timer = 0
    return shuffle, timer


async def begin_quiz(bot: Bot, chat, user, quiz_id: int, count: int,
                     mode: str = "exam", retry: bool = False):
    await db.ensure_user(user.id, user.username, user.first_name)
    is_group = getattr(chat, "type", "private") in ("group", "supergroup")
    key = chat.id

    if sessions.get(key):
        await bot.send_message(key, "⏳ Bu yerda test allaqachon ketyapti. Avval /stop qiling.")
        return

    if retry:
        src_items = last_wrong.get(user.id) or []
        if not src_items:
            await bot.send_message(key, "✅ Xato savol qolmagan!")
            return
        src = [it["q"] for it in src_items]
        quiz_name = "Xatolar ustida ishlash"
        real_quiz_id = src[0].get("_quiz_id", 0)
        count = 0
        mode = "practice"
    else:
        quiz = await db.get_quiz(quiz_id)
        if not quiz:
            await bot.send_message(key, "Test topilmadi 😕")
            return
        src = await db.get_questions(quiz_id)
        if not src:
            await bot.send_message(key, "Bu testda savol yo'q.")
            return
        quiz_name = quiz["name"]
        real_quiz_id = quiz_id

    _cleanup_session(key)
    shuffle, cfg_timer = await _game_settings()
    if is_group:
        gmode = "group"
        timer = cfg_timer or GROUP_DEFAULT_TIMER
    else:
        gmode = "private"
        timer = 0 if mode == "practice" else (cfg_timer or EXAM_DEFAULT_TIMER)

    prepared = _prepare(src, count, shuffle)
    for q in prepared:
        q["_quiz_id"] = real_quiz_id

    sessions[key] = {
        "mode": gmode,
        "play_mode": "practice" if (gmode == "private" and mode == "practice") else "exam",
        "quiz_id": real_quiz_id,
        "quiz_name": quiz_name,
        "questions": prepared,
        "index": 0,
        "chat_id": key,
        "timer": timer,
        "current_poll": None,
        "timer_task": None,
        "scores": {},
        "names": {},
        "answered": set(),
        "wrong": {},
        "speed": {},
        "round": {"correct": [], "wrong": []},
        "first_correct": None,
        "starter": user.id,
        "paused": False,
        "started_at": time.monotonic(),
    }
    mode_label = "🎓 Mashq" if sessions[key]["play_mode"] == "practice" else "📝 Imtihon"
    extra = f" · ⏱ {timer}s/savol" if timer else " · ⏱ vaqtsiz"
    who = "👥 Guruh testi" if is_group else mode_label
    try:
        await bot.send_message(
            key,
            f"{who}: <b>{_esc(quiz_name)}</b>\n"
            f"📋 Savollar: {len(prepared)}{extra}\n⏹ To'xtatish: /stop",
        )
    except Exception:
        log.exception("begin_quiz xabar yuborilmadi")
        _cleanup_session(key)
        return
    await send_question(bot, key)


def _progress_bar(cur: int, total: int, width: int = 10) -> str:
    filled = max(0, min(width, round(cur / total * width))) if total else 0
    return "▰" * filled + "▱" * (width - filled)


async def send_question(bot: Bot, key: int):
    s = sessions.get(key)
    if not s:
        return
    idx = s["index"]
    questions = s["questions"]
    if idx >= len(questions):
        await finish_quiz(bot, key)
        return

    s["answered"] = set()
    s["round"] = {"correct": [], "wrong": []}
    s["first_correct"] = None
    q = questions[idx]

    # rasmli savol bo'lsa — avval rasm
    if q.get("image_file_id"):
        try:
            await bot.send_photo(s["chat_id"], q["image_file_id"],
                                 caption=f"🖼 {idx + 1}-savol")
        except Exception:
            log.warning("Savol rasmi yuborilmadi")

    bar = _progress_bar(idx + 1, len(questions))
    q_head = f"{bar} {idx + 1}/{len(questions)}\n"
    q_text = (q_head + q["text"])[: settings.QUESTION_LIMIT]
    options = [str(o)[: settings.OPTION_LIMIT] for o in q["options"][: settings.MAX_OPTIONS]]
    correct = q["correct"] if 0 <= q["correct"] < len(options) else 0

    timer = s["timer"]
    kwargs = {}
    if timer and 5 <= timer <= 600:
        kwargs["open_period"] = timer
    # izoh: mashq rejimida darhol ko'rsatiladi (imtihon/guruhda oxirida)
    if q.get("explanation") and s["play_mode"] == "practice":
        kwargs["explanation"] = str(q["explanation"])[:200]

    try:
        msg = await bot.send_poll(
            chat_id=s["chat_id"],
            question=q_text,
            options=options,
            type=PollType.QUIZ,
            correct_option_id=correct,
            is_anonymous=False,
            **kwargs,
        )
    except Exception:
        log.exception("send_poll xato — sessiya to'xtatildi")
        _cleanup_session(key)
        try:
            await bot.send_message(key, "⚠️ Savol yuborilmadi, test to'xtatildi.")
        except Exception:
            pass
        return

    s["current_poll"] = msg.poll.id
    s["q_start"] = time.monotonic()
    poll_map[msg.poll.id] = key

    if timer and 5 <= timer <= 600:
        s["timer_task"] = asyncio.create_task(_timeout(bot, key, msg.poll.id, timer + 3))


async def _timeout(bot: Bot, key: int, poll_id: str, delay: int):
    try:
        await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return
    s = sessions.get(key)
    if s and s.get("current_poll") == poll_id:
        await advance(bot, key)


async def advance(bot: Bot, key: int):
    s = sessions.get(key)
    if not s:
        return
    task = s.get("timer_task")
    if task:
        task.cancel()
        s["timer_task"] = None
    pid = s.get("current_poll")
    if pid:
        poll_map.pop(pid, None)
    s["current_poll"] = None

    # guruhda savoldan keyin jonli tabel
    if s["mode"] == "group":
        await _group_round_report(bot, key)

    # pauza (shaxsiy): keyingi savolni yubormay kutamiz
    if s["mode"] == "private" and s.get("paused"):
        s["_await_resume"] = True
        try:
            await bot.send_message(
                key, "⏸ <b>Pauza.</b> Davom etish uchun tugmani bosing yoki /davom.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="▶️ Davom ettirish", callback_data="resume")]]))
        except Exception:
            pass
        return

    s["index"] += 1
    await asyncio.sleep(0.4)
    await send_question(bot, key)


async def _resume(bot: Bot, key: int):
    s = sessions.get(key)
    if not s or not s.get("_await_resume"):
        await bot.send_message(key, "Davom ettiriladigan pauza yo'q.")
        return
    s["paused"] = False
    s["_await_resume"] = False
    s["index"] += 1
    await send_question(bot, key)


async def _group_round_report(bot: Bot, key: int):
    s = sessions.get(key)
    if not s:
        return
    rnd = s.get("round", {"correct": [], "wrong": []})
    nc, nw = len(rnd["correct"]), len(rnd["wrong"])
    if nc == 0 and nw == 0:
        return  # hech kim javob bermadi — jim o'tamiz
    fc = s.get("first_correct")
    lines = [f"📊 {s['index'] + 1}-savol: ✅ {nc} to'g'ri · ❌ {nw} xato"]
    if fc is not None:
        lines.append(f"⚡ Eng tez: {s['names'].get(fc, fc)}")
    # joriy top-3
    ranking = sorted(s["scores"].items(),
                     key=lambda kv: (-kv[1], s["speed"].get(kv[0], 9e9)))[:3]
    if ranking:
        medals = ["🥇", "🥈", "🥉"]
        tops = "  ".join(f"{medals[i]}{s['names'].get(uid, uid)}·{sc}"
                         for i, (uid, sc) in enumerate(ranking))
        lines.append(tops)
    try:
        await bot.send_message(key, "\n".join(lines))
    except Exception:
        pass


def _grade(pct: int):
    if pct >= 90:
        return "🏆", "A", "Ajoyib natija!"
    if pct >= 70:
        return "🎉", "B", "Yaxshi ish!"
    if pct >= 50:
        return "👍", "C", "Yomon emas."
    return "📚", "D", "Yana mashq qiling."


def _fmt_dur(sec) -> str:
    if not sec:
        return ""
    sec = int(sec)
    m, s = divmod(sec, 60)
    return f"{m}m {s}s" if m else f"{s}s"


async def finish_quiz(bot: Bot, key: int):
    s = sessions.pop(key, None)
    if not s:
        return
    total = len(s["questions"])
    duration = int(time.monotonic() - s.get("started_at", time.monotonic()))

    # natijalarni bazaga yozamiz
    for uid, sc in s["scores"].items():
        try:
            await db.save_attempt(uid, s["names"].get(uid), s["quiz_id"], s["quiz_name"],
                                  sc, total,
                                  mode=s["play_mode"] if s["mode"] == "private" else "group",
                                  duration_sec=duration if uid == s["starter"] else None)
        except Exception:
            log.exception("save_attempt xato (uid=%s)", uid)

    if s["mode"] == "group":
        await _finish_group(bot, s, total)
        return

    # ── shaxsiy rejim ──
    uid = s["starter"]
    score = s["scores"].get(uid, 0)
    pct = round(score / total * 100) if total else 0
    wrong = s["wrong"].get(uid, [])
    emoji, grade, note = _grade(pct)

    # gamifikatsiya
    xp = game.xp_for_attempt(score, total, s["play_mode"])
    new_total_xp = await db.add_xp(uid, xp)
    before = game.level_for_xp(new_total_xp - xp)["level"]
    after_lvl = game.level_for_xp(new_total_xp)
    streak = await db.touch_streak(uid)
    new_ach = await _check_achievements(uid, score, total, streak)

    # natija matni
    dur = _fmt_dur(duration)
    lines = [
        f"{emoji} <b>Test yakunlandi!</b>",
        f"📝 {_esc(s['quiz_name'])}",
        "",
        f"✅ To'g'ri: <b>{score}/{total}</b>  ·  📊 <b>{pct}%</b>  ·  Baho: <b>{grade}</b>",
    ]
    if dur:
        lines.append(f"⏱ Vaqt: {dur}")
    lines.append(f"✨ +{xp} XP  ·  🔥 Streak: {streak['streak']} kun")
    if after_lvl["level"] > before:
        lines.append(f"🎉 <b>Yangi daraja!</b> {after_lvl['title']} ({after_lvl['level']}-daraja)")
    lines.append(f"\n<i>{note}</i>")

    # natija kartochkasi (rasm) — bo'lsa
    display = (s["names"].get(uid) or "").lstrip("@") or "Foydalanuvchi"
    png = cards.make_result_card(display, s["quiz_name"], score, total, pct)

    rows = []
    if wrong:
        last_wrong[uid] = wrong
        rows.append([InlineKeyboardButton(
            text=f"❌ Xatolar ustida ({len(wrong)})", callback_data="retry")])
    rows.append([
        InlineKeyboardButton(text="🔁 Qayta", callback_data=f"pick:{s['quiz_id']}"),
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"rank:{s['quiz_id']}:all"),
    ])
    rows.append([
        InlineKeyboardButton(text="📊 Profilim", callback_data="prof"),
        InlineKeyboardButton(text="📚 Testlar", callback_data="cats"),
    ])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    caption = "\n".join(lines)
    if png:
        try:
            await bot.send_photo(s["chat_id"], BufferedInputFile(png, "natija.png"),
                                 caption=caption, reply_markup=kb)
        except Exception:
            await bot.send_message(s["chat_id"], caption, reply_markup=kb)
    else:
        await bot.send_message(s["chat_id"], caption, reply_markup=kb)

    # yangi nishonlar bildirishnomasi
    if new_ach:
        txt = "🎖 <b>Yangi nishon(lar)!</b>\n" + "\n".join(game.achievement_line(c) for c in new_ach)
        await bot.send_message(s["chat_id"], txt)

    # xatolar tahlilini alohida yuboramiz (izohlar bilan)
    if wrong and s["play_mode"] != "practice":
        await _send_long(bot, s["chat_id"], _wrong_analysis(wrong))


async def _group_participant_reward(uid: int, score: int, total: int) -> None:
    """Guruh ishtirokchisiga XP/streak/nishon beradi (fon vazifasi, jimgina)."""
    await db.add_xp(uid, game.xp_for_attempt(score, total, "exam"))
    streak = await db.touch_streak(uid)
    await _check_achievements(uid, score, total, streak)


async def _finish_group(bot: Bot, s: dict, total: int):
    ranking = sorted(s["scores"].items(),
                     key=lambda kv: (-kv[1], s["speed"].get(kv[0], 9e9)))
    if not ranking:
        await bot.send_message(s["chat_id"], "👥 Test tugadi. Hech kim javob bermadi 🤷")
        return
    # ishtirokchilarga XP + streak + nishonlar (jimgina, profil orqali ko'rinadi)
    for uid, sc in ranking:
        _bg(_group_participant_reward(uid, sc, total))
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"👥 <b>{_esc(s['quiz_name'])}</b> — yakuniy natijalar:\n"]
    for i, (uid, sc) in enumerate(ranking):
        m = medals[i] if i < 3 else f"{i+1}."
        pct = round(sc / total * 100) if total else 0
        lines.append(f"{m} {_esc(str(s['names'].get(uid, uid)))} — <b>{sc}/{total}</b> ({pct}%)")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔁 Yana", callback_data=f"pick:{s['quiz_id']}"),
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"rank:{s['quiz_id']}:all")]])
    await bot.send_message(s["chat_id"], "\n".join(lines), reply_markup=kb)


def _wrong_analysis(wrong: list) -> str:
    lines = ["📋 <b>Xatolar tahlili:</b>\n"]
    for i, item in enumerate(wrong[:20], 1):
        q = item["q"]
        ch = item.get("chosen", -1)
        opts = q["options"]
        your = opts[ch] if 0 <= ch < len(opts) else "— (javobsiz / vaqt tugadi)"
        corr = opts[q["correct"]] if 0 <= q["correct"] < len(opts) else "?"
        lines.append(f"<b>{i}. {_esc(q['text'])}</b>")
        lines.append(f"   ❌ Siz: {_esc(your)}")
        lines.append(f"   ✅ To'g'ri: {_esc(corr)}")
        if q.get("explanation"):
            lines.append(f"   💡 {_esc(q['explanation'])}")
        lines.append("")
    if len(wrong) > 20:
        lines.append(f"…va yana {len(wrong) - 20} ta xato savol.")
    return "\n".join(lines)


async def _check_achievements(uid: int, score: int, total: int, streak: dict) -> list:
    """Shartlarga mos nishonlarni beradi va yangilar ro'yxatini qaytaradi."""
    new = []
    try:
        prof = await db.user_profile(uid)
        attempts = prof.get("attempts") or 0
        quizzes = prof.get("quizzes") or 0
        correct_total = await db.correct_answers_total(uid)
        checks = []
        if attempts >= 1:
            checks.append("first_quiz")
        if attempts >= 10:
            checks.append("ten_quizzes")
        if attempts >= 50:
            checks.append("fifty_quizzes")
        if attempts >= 100:
            checks.append("hundred_quizzes")
        if total and score == total:
            checks.append("perfect")
        if quizzes >= 5:
            checks.append("explorer")
        if quizzes >= 15:
            checks.append("scholar")
        st = streak.get("streak", 0)
        if st >= 3:
            checks.append("streak3")
        if st >= 7:
            checks.append("streak7")
        if st >= 30:
            checks.append("streak30")
        if correct_total >= 100:
            checks.append("centurion")
        if correct_total >= 500:
            checks.append("sharpshooter")
        for code in checks:
            if await db.grant_achievement(uid, code):
                new.append(code)
    except Exception:
        log.exception("Nishon tekshiruvi xato")
    return new
