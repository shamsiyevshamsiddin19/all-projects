"""@tatulmsbot — TUIT LMS yordamchi bot (aiogram 3)."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, FSInputFile, Message

from core import db
from core.config import BASE_DIR, settings
from core.util import esc
from lms import session, stats
from lms.client import LmsError, LoginError
from lms.session import NotRegistered
from . import keyboards as kb
from . import texts as T

log = logging.getLogger("lms_bot")
router = Router(name="lms")
TZ = ZoneInfo(settings.tz)

# start xabari rasmi (bir marta yuklab, file_id keshlanadi — keyingi safar tez)
START_IMG = BASE_DIR / "image" / "Gemini_Generated_Image_vq2p6kvq2p6kvq2p.png"
_start_photo_id: str | None = None


async def _send_start(m: Message, caption: str, logged_in: bool):
    """/start — rasm + inline tugmalar bilan yuboradi (file_id keshlanadi)."""
    global _start_photo_id
    markup = kb.start_kb(logged_in)
    photo = _start_photo_id or (FSInputFile(START_IMG) if START_IMG.exists() else None)
    if photo is None:
        await m.answer(caption, reply_markup=markup)
        return
    try:
        msg = await m.answer_photo(photo, caption=caption, reply_markup=markup)
        if _start_photo_id is None and msg.photo:
            _start_photo_id = msg.photo[-1].file_id  # keyingi safar qayta yuklamaymiz
    except Exception as e:  # noqa: BLE001
        log.warning("start photo: %s", e)
        await m.answer(caption, reply_markup=markup)


async def _typing(m: Message):
    """Foydalanuvchiga darhol 'yozyapti…' ko'rsatkichi (kutish sezilmasin)."""
    try:
        await m.bot.send_chat_action(m.chat.id, "typing")
    except Exception:  # noqa: BLE001
        pass


async def _prewarm(uid: int):
    """Login'dan keyin fonda ma'lumotni oldindan yuklab, keshni isitib qo'yamiz —
    birinchi tugma bosilganda tayyor turadi."""
    try:
        c = await session.get_session(uid)
        await asyncio.gather(
            c.courses(), c.schedule_active(tz=TZ), c.study_plan(),
            return_exceptions=True)
    except Exception as e:  # noqa: BLE001
        log.info("prewarm uid=%s: %s", uid, e)

WELCOME = (
    "<b>TUIT LMS yordamchisi</b>\n"
    "<i>Muhammad al-Xorazmiy nomidagi TATU</i>\n\n"
    "Assalomu alaykum! Men orqali butun LMS hisobingizni Telegramning o'zidan boshqarasiz:\n\n"
    "📅 <b>Dars jadvali</b> — kunlik va haftalik\n"
    "📚 <b>Fanlar va baholar</b> — har bir topshiriq bo'yicha\n"
    "📦 <b>Resurslar</b> — ma'ruza va amaliyot fayllarini bitta tugma bilan\n"
    "⏰ <b>Deadline eslatmalari</b> — endi hech narsani o'tkazib yubormaysiz\n"
    "📋 <b>Davomat</b> · 🏆 <b>Yakuniy imtihonlar</b> · 📈 <b>Umumiy ball</b>\n\n"
    "Boshlash uchun LMS hisobingizga kiring:\n👉 /login"
)
HELP = (
    "<b>Yordam — TUIT LMS bot</b>\n\n"
    "<b>Buyruqlar</b>\n"
    "/login — LMS hisobiga kirish\n"
    "/menu — asosiy menyu\n"
    "/logout — hisobdan chiqish\n"
    "/help — ushbu yordam\n\n"
    "<b>Imkoniyatlar</b>\n"
    "• Pastdagi tugmalar orqali jadval, baholar, resurslar va boshqalarni oching\n"
    "• Har kuni ertalab bugungi jadval avtomatik yuboriladi\n"
    "• Topshiriq muddati yaqinlashganda ogohlantiraman\n"
    "• Istalgan chatda <code>@tatulmsbot</code> deb yozib, jadval yoki baholaringizni ulashing\n\n"
    "🔒 Parolingiz <b>shifrlangan</b> holda saqlanadi, hech kimga ko'rsatilmaydi va faqat LMS'ga kirish uchun ishlatiladi."
)


class Login(StatesGroup):
    login = State()
    password = State()


# ─────────────────────── start / login ───────────────────────
@router.message(CommandStart())
async def start(m: Message, command: CommandObject, state: FSMContext):
    u = await db.get_user(m.from_user.id)
    if (command.args or "") == "login" and not (u and u.get("login")):
        await login_start(m, state)
        return
    if u and u.get("login"):
        await _send_start(
            m,
            f"Xush kelibsiz, <b>{esc(u.get('full_name') or '')}</b>!\n"
            "Quyidagi tugmalardan yoki pastdagi menyudan foydalaning 👇",
            logged_in=True)
        await m.answer("🏠 Asosiy menyu:", reply_markup=kb.main_menu())
    else:
        await _send_start(m, WELCOME, logged_in=False)


@router.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer(HELP)


@router.message(Command("menu"))
async def menu_cmd(m: Message):
    await m.answer("🏠 Asosiy menyu:", reply_markup=kb.main_menu())


# ─────────────────────── start inline tugmalari ───────────────────────
@router.callback_query(F.data == "start:login")
async def cb_start_login(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(Login.login)
    await cq.message.answer(
        "🔑 LMS <b>login</b>ingizni yuboring (masalan: <code>1BK30552</code>):")


@router.callback_query(F.data == "start:help")
async def cb_start_help(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer(HELP)


@router.callback_query(F.data == "start:today")
async def cb_start_today(cq: CallbackQuery):
    await cq.answer("Jadval tayyorlanyapti…")
    await _do_schedule(cq.message, cq.from_user.id, "today")


@router.message(Command("login"))
async def login_start(m: Message, state: FSMContext):
    await state.set_state(Login.login)
    await m.answer("🔑 LMS <b>login</b>ingizni yuboring (masalan: <code>1BK30552</code>):")


@router.message(Login.login)
async def login_get(m: Message, state: FSMContext):
    await state.update_data(login=m.text.strip())
    await state.set_state(Login.password)
    await m.answer("🔒 Endi <b>parol</b>ingizni yuboring.\n"
                   "<i>(Xavfsizlik uchun xabaringizni darhol o'chiraman)</i>")


@router.message(Login.password)
async def login_password(m: Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("login", "")
    password = m.text or ""
    # parolni chatdan o'chirish
    try:
        await m.delete()
    except Exception:  # noqa: BLE001
        pass
    wait = await m.answer("⏳ Tekshirilyapti…")
    try:
        full_name = await session.verify_login(login, password)
    except LoginError:
        await wait.edit_text("❌ Login yoki parol xato. Qaytadan /login")
        await state.clear()
        return
    except Exception as e:  # noqa: BLE001
        log.exception("login verify")
        await wait.edit_text(f"⚠️ Xatolik: {esc(str(e))}\nQaytadan /login")
        await state.clear()
        return

    await db.save_credentials(m.from_user.id, login, password, service="lms",
                              full_name=full_name, tg_username=m.from_user.username or "")
    await state.clear()
    # reyting uchun statistikani yig'amiz (GPA, fan baholari)
    try:
        c = await session.get_session(m.from_user.id)
        await stats.refresh(m.from_user.id, c)
    except Exception as e:  # noqa: BLE001
        log.info("login stats refresh: %s", e)
    await wait.edit_text(f"✅ Muvaffaqiyatli kirdingiz!\n👤 <b>{esc(full_name)}</b>")
    await m.answer("Asosiy menyu 👇", reply_markup=kb.main_menu())
    # fonda ma'lumotni oldindan yuklab qo'yamiz — birinchi tugma tez ochiladi
    asyncio.create_task(_prewarm(m.from_user.id))


@router.message(Command("logout"))
async def logout_cmd(m: Message):
    await m.answer("Hisobdan chiqishni tasdiqlang:", reply_markup=kb.confirm_logout_kb())


# ─────────────────────── helper ───────────────────────
async def _guard(m_or_cq) -> session.LmsClient | None:
    """Sessiya oladi yoki xato xabarini yuboradi."""
    uid = m_or_cq.from_user.id
    answer = m_or_cq.answer if isinstance(m_or_cq, Message) else m_or_cq.message.answer
    try:
        return await session.get_session(uid)
    except NotRegistered:
        await answer("Avval tizimga kiring: /login")
    except LoginError:
        await session.drop(uid)
        await answer("🔑 Sessiya yaroqsiz. Parol o'zgargan bo'lsa qayta kiring: /login")
    except Exception as e:  # noqa: BLE001
        log.exception("guard")
        await answer(f"⚠️ Ulanishda xatolik: {esc(str(e))}")
    return None


def _today() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


# ─────────────────────── menyu: jadval ───────────────────────
async def _do_schedule(target: Message, uid: int, mode: str):
    """mode: 'today' | 'week'. FAOL semestrni avtomatik aniqlaydi."""
    try:
        c = await session.get_session(uid)
    except NotRegistered:
        await target.answer("Avval tizimga kiring: /login")
        return
    except LoginError:
        await session.drop(uid)
        await target.answer("🔑 Sessiya yaroqsiz. Parol o'zgargan bo'lsa qayta kiring: /login")
        return
    except Exception as e:  # noqa: BLE001
        await target.answer(f"⚠️ Ulanishda xatolik: {esc(str(e))}")
        return
    wait = await target.answer("⏳ Jadval tayyorlanyapti…")
    try:
        items, sem_id, sem_name = await c.schedule_active(tz=TZ)
    except Exception as e:  # noqa: BLE001
        await wait.edit_text(f"⚠️ {esc(str(e))}")
        return
    if not sem_id:
        await wait.edit_text(
            "🎉 Hozircha faol semestr yo'q — darslar tugagan.\n"
            "Qayta o'qish (retake) boshlansa, avtomatik shu yerda ko'rsataman.")
        return
    txt = T.fmt_one_day(items, _today()) if mode == "today" else T.fmt_week(items)
    if "qayta" in (sem_name or "").lower():
        txt = "♻️ <i>Qayta o'qish semestri</i>\n\n" + txt
    await wait.edit_text(txt)


@router.message(F.text == "📅 Bugungi jadval")
async def today_schedule(m: Message):
    await _typing(m)
    await _do_schedule(m, m.from_user.id, "today")


@router.message(F.text == "🗓 Haftalik")
async def week_schedule(m: Message):
    await _typing(m)
    await _do_schedule(m, m.from_user.id, "week")


# ─────────────────────── menyu: fanlar ───────────────────────
async def _show_courses(target: Message, uid: int, action: str = "course"):
    c = await session.get_session(uid)
    courses = await c.courses()
    if not courses:
        await target.answer(T.fmt_courses(courses))
        return
    sem_name = await c._semester_name(courses[0].semester_id)
    await target.answer(T.fmt_courses(courses, sem_name),
                        reply_markup=kb.courses_kb(courses, action))


@router.message(F.text == "📚 Fanlarim")
async def my_courses(m: Message):
    await _typing(m)
    if not await _guard(m):
        return
    try:
        await _show_courses(m, m.from_user.id, "course")
    except Exception as e:  # noqa: BLE001
        await m.answer(f"⚠️ {esc(str(e))}")


@router.message(F.text == "📊 Baholar")
async def grades_menu(m: Message):
    await _typing(m)
    if not await _guard(m):
        return
    try:
        await _show_courses(m, m.from_user.id, "grades")
    except Exception as e:  # noqa: BLE001
        await m.answer(f"⚠️ {esc(str(e))}")


@router.message(F.text == "📦 Resurslar")
async def resources_menu(m: Message):
    await _typing(m)
    if not await _guard(m):
        return
    try:
        await _show_courses(m, m.from_user.id, "course")
    except Exception as e:  # noqa: BLE001
        await m.answer(f"⚠️ {esc(str(e))}")
    await m.answer("Fanni tanlab, kerakli resurs turini yuklang.")


@router.callback_query(F.data == "menu:courses")
async def cb_courses(cq: CallbackQuery):
    await cq.answer()
    if not await _guard(cq):
        return
    await _show_courses(cq.message, cq.from_user.id, "course")


@router.callback_query(F.data.startswith("course:"))
async def cb_course(cq: CallbackQuery):
    await cq.answer()
    c = await _guard(cq)
    if not c:
        return
    cid = int(cq.data.split(":")[1])
    await cq.message.answer("📘 Fan boshqaruvi 👇", reply_markup=kb.course_view_kb(cid))


# ─────────────────────── baholar ───────────────────────
@router.callback_query(F.data.startswith("grades:"))
async def cb_grades(cq: CallbackQuery):
    await cq.answer("Yuklanyapti…")
    c = await _guard(cq)
    if not c:
        return
    cid = int(cq.data.split(":")[1])
    try:
        courses = await c.courses()
        course = next((x for x in courses if x.id == cid), None)
        tasks = await c.course_tasks(cid, tz=TZ)
    except Exception as e:  # noqa: BLE001
        await cq.message.answer(f"⚠️ {esc(str(e))}")
        return
    if not course:
        await cq.message.answer("Fan topilmadi.")
        return
    await cq.message.answer(T.fmt_grades(course, tasks))


# ─────────────────────── resurslar yuklash ───────────────────────
async def _collect_files(c, cid: int, kind: str):
    tasks = await c.course_tasks(cid, tz=TZ)
    files = []
    for t in tasks:
        if kind == "lecture" and not t.is_lecture:
            continue
        if kind == "practice" and not t.is_practice:
            continue
        for f in t.files:
            files.append((t, f))
    return files


async def _send_files(bot: Bot, chat_id: int, c, files):
    if not files:
        await bot.send_message(chat_id, "📭 Bu turda fayl topilmadi.")
        return
    await bot.send_message(chat_id, f"📦 {len(files)} ta fayl yuklanyapti, biroz kuting…")
    sent, failed = 0, 0
    for t, f in files:
        try:
            name, data = await c.download(f.url)
            caption = f"📎 <b>{esc(t.name)}</b> · {esc(t.lesson_type)}"
            await _send_doc(bot, chat_id, data, name, caption)
            sent += 1
            await asyncio.sleep(0.4)
        except LmsError as e:
            failed += 1
            await bot.send_message(chat_id, f"⚠️ {esc(t.name)}: {esc(str(e))}\n🔗 {f.url}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            log.warning("file send: %s", e)
            await bot.send_message(chat_id, f"🔗 {esc(t.name)}: {f.url}")
    await bot.send_message(chat_id, f"✅ Tayyor. Yuborildi: {sent}" +
                           (f", o'tkazib yuborildi: {failed}" if failed else ""))


@router.callback_query(F.data.startswith("resall:"))
async def cb_resall(cq: CallbackQuery, bot: Bot):
    await cq.answer("Tayyorlanyapti…")
    c = await _guard(cq)
    if not c:
        return
    cid = int(cq.data.split(":")[1])
    try:
        files = await _collect_files(c, cid, "all")
        await _send_files(bot, cq.message.chat.id, c, files)
    except Exception as e:  # noqa: BLE001
        await cq.message.answer(f"⚠️ {esc(str(e))}")


@router.callback_query(F.data.startswith("res:"))
async def cb_res(cq: CallbackQuery, bot: Bot):
    await cq.answer("Tayyorlanyapti…")
    c = await _guard(cq)
    if not c:
        return
    _, cid, kind = cq.data.split(":")
    try:
        files = await _collect_files(c, int(cid), kind)
        await _send_files(bot, cq.message.chat.id, c, files)
    except Exception as e:  # noqa: BLE001
        await cq.message.answer(f"⚠️ {esc(str(e))}")


# ─────────────── kalendar reja resurslari (ustoz materiallari) ───────────────
_FNAME_BAD = re.compile(r'[\\/:*?"<>|\n\r\t]+')


def _safe_filename(title: str, ext: str) -> str:
    name = _FNAME_BAD.sub("_", (title or "resurs")).strip().strip(".")[:80] or "resurs"
    if ext and not name.lower().endswith("." + ext):
        name = f"{name}.{ext}"
    return name


async def _send_doc(bot: Bot, chat_id: int, data: bytes, filename: str, caption: str):
    try:
        await bot.send_document(chat_id, BufferedInputFile(data, filename=filename),
                                caption=caption)
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after + 1)
        await bot.send_document(chat_id, BufferedInputFile(data, filename=filename),
                                caption=caption)


async def _send_links(bot: Bot, chat_id: int, links):
    if not links:
        return
    lines = ["🔗 <b>Foydali havolalar</b>\n"]
    seen = set()
    for r in links:
        if r.url in seen:
            continue
        seen.add(r.url)
        label = esc(r.title if r.title and r.title != "URL" else (r.topic[:50] or r.url))
        lines.append(f"• <a href=\"{esc(r.url)}\">{label}</a>")
    await bot.send_message(chat_id, "\n".join(lines), disable_web_page_preview=True)


@router.callback_query(F.data.startswith("cal:"))
async def cb_calendar(cq: CallbackQuery, bot: Bot):
    await cq.answer("Tayyorlanyapti…")
    c = await _guard(cq)
    if not c:
        return
    _, cid, kind = cq.data.split(":")
    chat_id = cq.message.chat.id
    try:
        resources = await c.calendar_resources(int(cid))
    except Exception as e:  # noqa: BLE001
        await cq.message.answer(f"⚠️ {esc(str(e))}")
        return

    if kind == "links":
        links = [r for r in resources if r.is_external]
        if not links:
            await bot.send_message(chat_id, "📭 Foydali havola topilmadi.")
        else:
            await _send_links(bot, chat_id, links)
        return

    # kind: lecture | practice — fayllarni yuklaymiz (takrorlarni olib tashlab)
    want = [r for r in resources if r.kind == kind and not r.is_external]
    seen, files = set(), []
    for r in want:
        if r.url in seen:
            continue
        seen.add(r.url)
        files.append(r)
    label = "Ma'ruza resurslari" if kind == "lecture" else "Amaliyot resurslari"
    if not files:
        await bot.send_message(chat_id, f"📭 {label} topilmadi.")
        return
    await bot.send_message(chat_id, f"📦 <b>{label}</b>: {len(files)} ta fayl yuklanyapti, "
                                    "biroz kuting…")
    sent, failed = 0, 0
    for r in files:
        try:
            _, data = await c.download(r.url)
            caption = f"📚 <b>{esc(r.title)}</b>"
            if r.topic:
                caption += f"\n<i>{esc(r.topic[:150])}</i>"
            await _send_doc(bot, chat_id, data, _safe_filename(r.title, r.ext), caption)
            sent += 1
            await asyncio.sleep(0.5)
        except LmsError as e:
            failed += 1
            await bot.send_message(chat_id, f"⚠️ {esc(r.title)}: {esc(str(e))}\n🔗 {esc(r.url)}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            log.warning("calendar file: %s", e)
            await bot.send_message(chat_id, f"🔗 {esc(r.title)}: {esc(r.url)}")
    msg = f"✅ Tayyor. Yuborildi: {sent}"
    if failed:
        msg += f", havola sifatida: {failed}"
    await bot.send_message(chat_id, msg)


# ─────────────────────── deadline'lar ───────────────────────
@router.message(F.text == "⏰ Deadline'lar")
async def deadlines(m: Message):
    c = await _guard(m)
    if not c:
        return
    wait = await m.answer("⏳ Topshiriqlar tekshirilyapti…")
    now = datetime.now(TZ)
    pairs = []
    try:
        courses = await c.courses()
        for course in courses:
            tasks = await c.course_tasks(course.id, tz=TZ)
            for t in tasks:
                if t.deadline and t.deadline > now and not t.graded:
                    pairs.append((course.subject, t))
    except Exception as e:  # noqa: BLE001
        await wait.edit_text(f"⚠️ {esc(str(e))}")
        return
    await wait.edit_text(T.fmt_deadlines(pairs, now))


# ─────────────────────── davomat ───────────────────────
@router.message(F.text == "📋 Davomat")
async def attendance(m: Message):
    c = await _guard(m)
    if not c:
        return
    wait = await m.answer("⏳ Davomat tekshirilyapti…")
    try:
        courses = await c.courses()
        missed = await c.attendance(subject_id=courses[0].id if courses else None)
    except Exception as e:  # noqa: BLE001
        await wait.edit_text(f"⚠️ {esc(str(e))}")
        return
    await wait.edit_text(T.fmt_attendance(courses, missed),
                         reply_markup=kb.courses_kb(courses, "miss") if missed else None)


@router.callback_query(F.data.startswith("miss:"))
async def cb_miss(cq: CallbackQuery):
    await cq.answer("Yuklanyapti…")
    c = await _guard(cq)
    if not c:
        return
    cid = int(cq.data.split(":")[1])
    try:
        courses = await c.courses()
        course = next((x for x in courses if x.id == cid), None)
        missed = await c.attendance(subject_id=cid)
    except Exception as e:  # noqa: BLE001
        await cq.message.answer(f"⚠️ {esc(str(e))}")
        return
    subj = course.subject if course else ""
    lessons = [m for m in missed if m.subject == subj]
    await cq.message.answer(T.fmt_missed_detail(subj, lessons))


# ─────────────────────── yakuniy imtihon ───────────────────────
@router.message(F.text == "🏆 Yakuniy")
async def finals(m: Message):
    await _typing(m)
    c = await _guard(m)
    if not c:
        return
    try:
        fin = await c.finals_list()
    except Exception as e:  # noqa: BLE001
        await m.answer(f"⚠️ {esc(str(e))}")
        return
    await m.answer(T.fmt_finals(fin))


# ─────────────────────── umumiy ko'rsatkich ───────────────────────
@router.message(F.text == "📈 Umumiy")
async def overall(m: Message):
    c = await _guard(m)
    if not c:
        return
    wait = await m.answer("⏳ Hisoblanyapti…")
    items = []
    gpa = None
    try:
        sp = await c.study_plan()
        gpa = sp.gpa
        courses = await c.courses()
        for course in courses:
            tasks = await c.course_tasks(course.id, tz=TZ)
            total = sum(float(t.score) for t in tasks if t.score is not None)
            mx = sum(float(t.max_score) for t in tasks if t.max_score is not None)
            items.append((course.subject, total, mx))
    except Exception as e:  # noqa: BLE001
        await wait.edit_text(f"⚠️ {esc(str(e))}")
        return
    await wait.edit_text(T.fmt_overall(items, gpa))


# ─────────────────────── reyting ───────────────────────
@router.message(F.text == "🏅 Reyting")
async def rating(m: Message):
    c = await _guard(m)
    if not c:
        return
    wait = await m.answer("⏳ Reyting tayyorlanyapti…")
    try:
        p = await c.profile()
        sp = await c.study_plan()
        await stats.save_from(m.from_user.id, p, sp)
    except Exception as e:  # noqa: BLE001
        await wait.edit_text(f"⚠️ {esc(str(e))}")
        return
    if sp.gpa is None:
        await wait.edit_text("GPA topilmadi (study-plan'da baholar yo'q bo'lishi mumkin).")
        return
    await wait.edit_text(
        f"🏅 <b>Reyting</b>\n\n⭐️ Sizning GPA: <b>{sp.gpa}</b>\n\n"
        "<i>Reyting botga ro'yxatdan o'tgan talabalar orasida hisoblanadi — "
        "qancha ko'p talaba qo'shilsa, shuncha aniq bo'ladi.</i>\n\n"
        "Qaysi bo'yicha ko'rasiz? 👇",
        reply_markup=kb.rating_kb())


@router.callback_query(F.data.startswith("rank:"))
async def cb_rank(cq: CallbackQuery):
    await cq.answer("Hisoblanyapti…")
    uid = cq.from_user.id
    scope = cq.data.split(":")[1]
    if scope == "subjects":
        ranks = await db.subject_ranking(uid)
        await cq.message.answer(T.fmt_subject_ranks(ranks))
        return
    res = await db.ranking(uid, scope)
    if not res:
        await cq.message.answer("Avval 🏅 <b>Reyting</b> tugmasini bosing (GPA yangilanishi kerak).")
        return
    me = await db.get_student_stats(uid) or {}
    extra = {
        "speciality": me.get("speciality") or "",
        "level": f"{me.get('level')}-kurs" if me.get("level") else "",
        "patok": f"{me.get('patok')}-potok" if me.get("patok") else "",
        "group": me.get("groupname") or "",
    }.get(scope, "")
    await cq.message.answer(T.fmt_rank(res, extra))


# ─────────────────────── GPA kalkulyatori ───────────────────────
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
          "VII": 7, "VIII": 8, "IX": 9, "X": 10}


def _kurs_of(semester: str) -> int:
    """Semestr (rim raqami: I, II, ...) -> kurs. I,II->1; III,IV->2; ..."""
    n = _ROMAN.get((semester or "").strip().upper(), 0)
    return (n + 1) // 2 if n else 0


def _compute_gpa(grades, override=None):
    """Kredit bo'yicha o'rtacha baho (5-ballik). override=(idx, grade)."""
    num = den = 0.0
    for i, g in enumerate(grades):
        grade = override[1] if (override and override[0] == i) else g.grade
        if grade is not None:
            num += float(grade) * g.credit
            den += g.credit
    return round(num / den, 2) if den else None


def _shown_grades(sp, level: int):
    """Kurs bo'yicha ko'rsatiladigan fanlar (kelajak/baholanmagan kurslar yashiriladi)."""
    graded_kurs = {_kurs_of(g.semester) for g in sp.grades if g.grade is not None}

    def show(g):
        k = _kurs_of(g.semester)
        return k > 0 and (k in graded_kurs or (level and k <= level))
    grades = [g for g in sp.grades if show(g)]
    grades.sort(key=lambda g: (_kurs_of(g.semester), g.subject))
    return grades


def _gpa_breakdown(grades):
    """(umumiy GPA, [(kurs, gpa), ...])."""
    by_kurs: dict[int, list] = {}
    for g in grades:
        by_kurs.setdefault(_kurs_of(g.semester), []).append(g)
    per = [(k, _compute_gpa(by_kurs[k])) for k in sorted(by_kurs)]
    return _compute_gpa(grades), per


def _level_int(profile) -> int:
    digits = "".join(ch for ch in (getattr(profile, "level", "") or "") if ch.isdigit())
    return int(digits) if digits else 0


async def _gpa_head(c) -> tuple[str, list]:
    """GPA sarlavha matni + ko'rsatiladigan fanlar ro'yxatini tayyorlaydi."""
    sp = await c.study_plan()
    try:
        prof = await c.profile()
        level = _level_int(prof)
    except Exception:  # noqa: BLE001
        level = 0
    grades = _shown_grades(sp, level)
    overall, per = _gpa_breakdown(grades)
    lines = [f"🧮 <b>GPA kalkulyatori</b>\n",
             f"⭐️ <b>Umumiy GPA: {overall}</b>  <i>(rasmiy: {sp.gpa})</i>\n"]
    for k, g in per:
        lines.append(f"📚 <b>{k}-kurs:</b> {g if g is not None else '—'}")
    lines.append("\nFanni tanlab, faraziy baho bilan sinang 👇")
    return "\n".join(lines), grades


@router.message(F.text == "🧮 GPA kalkulyator")
async def gpa_calc(m: Message):
    await _typing(m)
    c = await _guard(m)
    if not c:
        return
    try:
        text, grades = await _gpa_head(c)
    except Exception as e:  # noqa: BLE001
        await m.answer(f"⚠️ {esc(str(e))}")
        return
    if not grades:
        await m.answer("Study-plan'da baholangan fanlar topilmadi.")
        return
    await m.answer(text, reply_markup=kb.gpa_subjects_kb(grades, _kurs_of))


@router.callback_query(F.data == "gpa:noop")
async def cb_gpa_noop(cq: CallbackQuery):
    await cq.answer()  # kurs sarlavhasi — hech narsa qilmaydi


@router.callback_query(F.data.startswith("gpasel:"))
async def cb_gpa_sel(cq: CallbackQuery):
    await cq.answer()
    c = await _guard(cq)
    if not c:
        return
    idx = int(cq.data.split(":")[1])
    _, grades = await _gpa_head(c)
    if idx >= len(grades):
        await cq.answer("Fan topilmadi", show_alert=True)
        return
    g = grades[idx]
    cur = f"{g.grade:g}" if g.grade is not None else "—"
    await cq.message.edit_text(
        f"🧮 <b>{esc(g.subject)}</b>\n"
        f"{_kurs_of(g.semester)}-kurs · hozirgi baho: <b>{cur}</b> · kredit: {g.credit}\n\n"
        "Bu fandan qanday baho olsangiz? 👇",
        reply_markup=kb.gpa_grades_kb(idx))


@router.callback_query(F.data.startswith("gpacalc:"))
async def cb_gpa_calc(cq: CallbackQuery):
    await cq.answer("Hisoblanyapti…")
    c = await _guard(cq)
    if not c:
        return
    _, idx_s, g_s = cq.data.split(":")
    idx, g = int(idx_s), int(g_s)
    _, grades = await _gpa_head(c)
    if idx >= len(grades):
        await cq.answer("Fan topilmadi", show_alert=True)
        return
    cur = _compute_gpa(grades)
    new = _compute_gpa(grades, override=(idx, g))
    subj = grades[idx].subject
    arrow = "📈" if (new or 0) > (cur or 0) else ("📉" if (new or 0) < (cur or 0) else "➡️")
    await cq.message.edit_text(
        "🧮 <b>GPA simulyatsiya</b>\n\n"
        f"📘 {esc(subj)} ({_kurs_of(grades[idx].semester)}-kurs) — faraziy baho: <b>{g}</b>\n\n"
        f"Umumiy GPA: <b>{cur}</b>\n{arrow} Yangi GPA: <b>{new}</b>\n\n"
        "<i>Taxminiy (5-ballik, kredit bo'yicha). Boshqa fanni sinash uchun pastdan tanlang.</i>",
        reply_markup=kb.gpa_subjects_kb(grades, _kurs_of))


@router.callback_query(F.data == "gpa:back")
async def cb_gpa_back(cq: CallbackQuery):
    await cq.answer()
    c = await _guard(cq)
    if not c:
        return
    text, grades = await _gpa_head(c)
    await cq.message.edit_text(text, reply_markup=kb.gpa_subjects_kb(grades, _kurs_of))


# ─────────────────────── profil ───────────────────────
@router.message(F.text == "👤 Profil")
async def profile(m: Message):
    await _typing(m)
    c = await _guard(m)
    if not c:
        return
    try:
        p = await c.profile()
        sp = await c.study_plan()
        await stats.save_from(m.from_user.id, p, sp)  # reyting bazasini yangilab qo'yamiz
    except Exception as e:  # noqa: BLE001
        await m.answer(f"⚠️ {esc(str(e))}")
        return
    await m.answer(T.fmt_profile(p, sp.gpa))


# ─────────────────────── sozlamalar ───────────────────────
@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(m: Message):
    u = await db.get_user(m.from_user.id)
    if not u:
        await m.answer("Avval tizimga kiring: /login")
        return
    await m.answer("⚙️ <b>Sozlamalar</b>", reply_markup=kb.settings_kb(u))


@router.callback_query(F.data == "menu:settings")
async def cb_settings(cq: CallbackQuery):
    await cq.answer()
    u = await db.get_user(cq.from_user.id)
    if u:
        await cq.message.edit_text("⚙️ <b>Sozlamalar</b>", reply_markup=kb.settings_kb(u))


@router.callback_query(F.data.in_({"set:morning", "set:deadline", "set:autosub", "set:changes"}))
async def cb_toggle(cq: CallbackQuery):
    field = {"set:morning": "morning_on", "set:deadline": "deadline_on",
             "set:autosub": "autosub_on", "set:changes": "changes_on"}[cq.data]
    u = await db.get_user(cq.from_user.id)
    if not u:
        await cq.answer("Avval /login")
        return
    new = 0 if u.get(field) else 1
    await db.set_field(cq.from_user.id, field, new)
    await cq.answer("Saqlandi")
    u = await db.get_user(cq.from_user.id)
    await cq.message.edit_text("⚙️ <b>Sozlamalar</b>", reply_markup=kb.settings_kb(u))


@router.callback_query(F.data == "set:semester")
async def cb_semester(cq: CallbackQuery):
    await cq.answer()
    c = await _guard(cq)
    if not c:
        return
    sems = await c.semesters()
    u = await db.get_user(cq.from_user.id)
    cur = (u or {}).get("semester_id") or None
    await cq.message.edit_text("🎓 Semestrni tanlang:", reply_markup=kb.semesters_kb(sems, cur))


@router.callback_query(F.data.startswith("sem:"))
async def cb_set_semester(cq: CallbackQuery):
    sid = int(cq.data.split(":")[1])
    await db.set_field(cq.from_user.id, "semester_id", sid)
    # o'zgarish-kuzatuv snapshotini tozalaymiz — yangi semestr uchun qayta asoslanadi
    await db.snapshot_clear(cq.from_user.id)
    await session.drop(cq.from_user.id)  # mijoz yangi semestrni oladi
    if sid:
        await cq.answer("Semestr tanlandi ✅")
        note = ("✅ <b>Semestr tanlandi.</b>\n\nEndi <b>fanlar, baholar, NB, dars jadvali, "
                "deadline'lar va resurslar</b> — barchasi shu semestr bo'yicha ko'rsatiladi. "
                "Qayta o'qish semestrini tanlasangiz — o'sha semestr ballari va NB'lari chiqadi.")
    else:
        await cq.answer("Avto rejim ✅")
        note = ("🔄 <b>Avto rejim.</b>\n\nJoriy (yoki tugagan bo'lsa — qayta o'qish) semestri "
                "avtomatik tanlanadi.")
    u = await db.get_user(cq.from_user.id)
    await cq.message.edit_text(note, reply_markup=kb.settings_kb(u))


@router.callback_query(F.data == "set:logout")
async def cb_logout(cq: CallbackQuery):
    await cq.answer()
    await cq.message.edit_text("Rostdan ham chiqasizmi?", reply_markup=kb.confirm_logout_kb())


@router.callback_query(F.data == "set:logout_yes")
async def cb_logout_yes(cq: CallbackQuery):
    await session.drop(cq.from_user.id)
    await db.delete_user(cq.from_user.id)
    await cq.answer("Chiqdingiz")
    await cq.message.edit_text("🚪 Hisobdan chiqdingiz. Qaytadan kirish: /login")


@router.callback_query(F.data == "menu:home")
async def cb_home(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer("🏠 Asosiy menyu 👇", reply_markup=kb.main_menu())
