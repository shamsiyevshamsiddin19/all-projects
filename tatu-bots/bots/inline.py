"""Inline rejim — istalgan chatda @tatulmsbot orqali jadval, deadline, baho,
fanlar/o'qituvchilar, GPA va profilni ulashish."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
)

from core.config import settings
from lms import session
from lms.session import NotRegistered
from . import texts as T

log = logging.getLogger("inline")
router = Router(name="inline")
TZ = ZoneInfo(settings.tz)

# uid -> (ts, data)  — har bosishda LMS'ni urmaslik uchun qisqa kesh
_cache: dict[int, tuple[float, dict]] = {}
_TTL = 30.0


def _content(text: str) -> InputTextMessageContent:
    return InputTextMessageContent(message_text=text, parse_mode="HTML",
                                   disable_web_page_preview=True)


def _ok(v, default):
    return default if isinstance(v, Exception) else v


async def _gather(uid: int) -> dict:
    now = time.time()
    hit = _cache.get(uid)
    if hit and now - hit[0] < _TTL:
        return hit[1]
    c = await session.get_session(uid)
    data: dict = {}
    # jadval (faol semestr)
    try:
        items, sem_id, sem_name = await c.schedule_active(tz=TZ)
        data["schedule"] = items
        data["sem_name"] = sem_name if sem_id else ""
    except Exception as e:  # noqa: BLE001
        log.info("inline schedule: %s", e)
        data["schedule"] = []
        data["sem_name"] = ""
    # profil + GPA + fanlar — bir vaqtda
    prof, sp, courses = await asyncio.gather(
        c.profile(), c.study_plan(), c.courses(), return_exceptions=True)
    data["profile"] = _ok(prof, None)
    sp = _ok(sp, None)
    data["gpa"] = sp.gpa if sp else None
    courses = _ok(courses, [])
    data["courses"] = courses
    # har fan vazifalari — bir vaqtda (deadline + baholar uchun)
    tasks_by: dict[int, list] = {}
    if courses:
        res = await asyncio.gather(
            *[c.course_tasks(co.id, tz=TZ) for co in courses],
            return_exceptions=True)
        for co, r in zip(courses, res):
            tasks_by[co.id] = _ok(r, [])
    data["tasks"] = tasks_by
    _cache[uid] = (now, data)
    return data


@router.inline_query()
async def inline(q: InlineQuery):
    uid = q.from_user.id
    try:
        data = await _gather(uid)
    except NotRegistered:
        await q.answer(
            [], cache_time=5, is_personal=True,
            button=InlineQueryResultsButton(text="🔑 Avval tizimga kiring — bosing",
                                            start_parameter="login"))
        return
    except Exception as e:  # noqa: BLE001
        log.warning("inline gather: %s", e)
        await q.answer([], cache_time=5, is_personal=True,
                       button=InlineQueryResultsButton(text="⚠️ Xatolik — botni oching",
                                                       start_parameter="start"))
        return

    now_dt = datetime.now(TZ)
    today = now_dt.strftime("%Y-%m-%d")
    sched = data.get("schedule") or []
    prof = data.get("profile")
    gpa = data.get("gpa")
    courses = data.get("courses") or []
    tasks_by = data.get("tasks") or {}

    # deadline'lar (kelajakdagi, baholanmagan)
    pairs = []
    for co in courses:
        for t in tasks_by.get(co.id, []):
            if t.deadline and t.deadline > now_dt and not t.graded:
                pairs.append((co.subject, t))

    # umumiy o'zlashtirish
    overall_items = []
    for co in courses:
        ts = tasks_by.get(co.id, [])
        total = sum(float(t.score) for t in ts if t.score is not None)
        mx = sum(float(t.max_score) for t in ts if t.max_score is not None)
        overall_items.append((co.subject, total, mx))

    results = [
        InlineQueryResultArticle(
            id="today", title="📅 Bugungi jadval",
            description="Bugungi darslar ro'yxati",
            input_message_content=_content(T.fmt_one_day(sched, today))),
        InlineQueryResultArticle(
            id="week", title="🗓 Haftalik jadval",
            description="Shu haftaning to'liq jadvali",
            input_message_content=_content(T.fmt_week(sched))),
    ]
    if pairs:
        results.append(InlineQueryResultArticle(
            id="deadlines", title="⏰ Deadline'lar",
            description=f"{len(pairs)} ta yaqin topshiriq muddati",
            input_message_content=_content(T.fmt_deadlines(pairs, now_dt))))
    if courses:
        results.append(InlineQueryResultArticle(
            id="courses", title="📚 Fanlar va o'qituvchilar",
            description=f"{len(courses)} ta fan · o'qituvchilar bilan",
            input_message_content=_content(T.fmt_courses(courses, data.get("sem_name", "")))))
        results.append(InlineQueryResultArticle(
            id="overall", title="📈 Umumiy o'zlashtirish",
            description="Har fan bo'yicha to'plangan ball",
            input_message_content=_content(T.fmt_overall(overall_items, gpa))))
    if gpa is not None:
        results.append(InlineQueryResultArticle(
            id="gpa", title=f"🏅 GPA: {gpa}",
            description="Sizning umumiy o'rtacha bahoyingiz",
            input_message_content=_content(
                f"🏅 <b>GPA (umumiy o'rtacha baho)</b>\n\n⭐️ <b>{gpa}</b>\n\n"
                "<i>@tatulmsbot orqali</i>")))
    if prof:
        results.append(InlineQueryResultArticle(
            id="profile", title="👤 Profilim",
            description=f"{prof.full_name} · {prof.group}",
            input_message_content=_content(T.fmt_profile(prof, gpa))))

    # qidiruv matni bo'yicha filtrlash
    query = (q.query or "").strip().lower()
    if query:
        filtered = [r for r in results if query in r.title.lower()
                    or query in (r.description or "").lower()]
        results = filtered or results

    await q.answer(results, cache_time=10, is_personal=True)
