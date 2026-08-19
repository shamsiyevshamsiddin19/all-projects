"""Rejalashtirilgan vazifalar: ertalabki jadval, deadline eslatmalari, avto-topshirish."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core import db
from core.config import settings
from core.util import esc, fmt_dt, time_left
from lms import session
from . import texts as T

log = logging.getLogger("scheduler")
TZ = ZoneInfo(settings.tz)


def _task_uid(course_id: int, task) -> str:
    dl = task.deadline.isoformat() if task.deadline else "?"
    return f"{course_id}:{task.name}:{dl}"


async def _user_session(uid: int):
    try:
        return await session.get_session(uid)
    except Exception as e:  # noqa: BLE001
        log.info("session yo'q (uid=%s): %s", uid, e)
        return None


# ─────────────────── ertalabki jadval ───────────────────
async def job_morning(bot: Bot):
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    for u in await db.all_users(service="lms"):
        if not u.get("morning_on"):
            continue
        c = await _user_session(u["tg_id"])
        if not c:
            continue
        try:
            # FAOL semestrni aniqlaymiz: semestr tugagan bo'lsa (sem_id None) —
            # yubormaymiz; qayta o'qish faol bo'lsa — o'shani avtomatik olamiz
            items, sem_id, sem_name = await c.schedule_active(tz=TZ)
            if not sem_id:
                continue  # faol semestr yo'q — darslar tugagan, bezovta qilmaymiz
            todays = [i for i in items if i.start and i.start.strftime("%Y-%m-%d") == today]
            if not todays:
                continue  # dam olish kuni — bezovta qilmaymiz
            head = "🌅 <b>Xayrli tong! Bugungi darslar:</b>\n\n"
            if "qayta" in (sem_name or "").lower():
                head = "🌅 <b>Xayrli tong!</b>\n♻️ <i>Qayta o'qish semestri</i> — bugungi darslar:\n\n"
            await bot.send_message(u["tg_id"], head + T.fmt_one_day(items, today))
        except Exception as e:  # noqa: BLE001
            log.warning("morning uid=%s: %s", u["tg_id"], e)


# ─────────────────── deadline eslatmalari ───────────────────
async def job_deadlines(bot: Bot):
    now = datetime.now(TZ)
    thresholds = sorted(settings.deadline_reminders)  # ascending
    for u in await db.all_users(service="lms"):
        if not u.get("deadline_on"):
            continue
        c = await _user_session(u["tg_id"])
        if not c:
            continue
        try:
            courses = await c.courses()
            for course in courses:
                tasks = await c.course_tasks(course.id, tz=TZ)
                for t in tasks:
                    if not t.deadline or t.deadline <= now or t.graded:
                        continue
                    minutes_left = (t.deadline - now).total_seconds() / 60
                    applicable = [th for th in thresholds if minutes_left <= th]
                    if not applicable:
                        continue
                    bucket = applicable[0]
                    uid_task = _task_uid(course.id, t)
                    if await db.reminder_already_sent(u["tg_id"], uid_task, bucket):
                        continue
                    await bot.send_message(
                        u["tg_id"],
                        f"⏰ <b>Deadline yaqin!</b>\n\n"
                        f"📘 {esc(course.subject)} · {esc(t.lesson_type)}\n"
                        f"📝 {esc(t.name)}\n"
                        f"📆 {fmt_dt(t.deadline)}\n"
                        f"⏳ <b>{time_left(t.deadline, now)}</b> qoldi!")
                    for th in thresholds:
                        if th >= bucket:
                            await db.mark_reminder_sent(u["tg_id"], uid_task, th)
        except Exception as e:  # noqa: BLE001
            log.warning("deadlines uid=%s: %s", u["tg_id"], e)


# ─────────────────── halol avto-topshirish ───────────────────
async def job_autosubmit(bot: Bot):
    """Talaba OLDINDAN bergan HAQIQIY faylni deadline'ga oz qolganda topshiradi.
    (Soxta bahona EMAS — talabaning o'z ishi.)"""
    now_ts = datetime.now(TZ).timestamp()
    for row in await db.pending_autosubmits():
        # deadline'ga <= 5 daqiqa qolganda topshiramiz
        if row["deadline"] - now_ts > 5 * 60:
            continue
        if row["deadline"] - now_ts < -60:  # muddat o'tib ketgan
            await db.set_autosubmit_status(row["id"], "failed")
            await bot.send_message(row["tg_id"],
                                   f"⚠️ <b>{esc(row['task_name'])}</b> — muddat o'tdi, topshirilmadi.")
            continue
        c = await _user_session(row["tg_id"])
        if not c:
            continue
        try:
            tg_file = await bot.get_file(row["file_id"])
            buf = await bot.download_file(tg_file.file_path)
            data = buf.read()
            res = await c.submit(row["submit_id"], data, row["file_name"])
            await db.set_autosubmit_status(row["id"], "done")
            await bot.send_message(
                row["tg_id"],
                f"🤖 <b>Avto-topshirildi!</b>\n📝 {esc(row['task_name'])}\n"
                f"📎 {esc(row['file_name'])}\n<i>{esc(str(res))[:120]}</i>")
        except Exception as e:  # noqa: BLE001
            log.warning("autosubmit id=%s: %s", row["id"], e)
            await db.set_autosubmit_status(row["id"], "failed")
            await bot.send_message(row["tg_id"],
                                   f"⚠️ Avto-topshirishda xatolik: {esc(str(e))}")


def _num(v) -> str:
    try:
        f = float(v)
        return str(int(f)) if f.is_integer() else f"{f:g}"
    except (TypeError, ValueError):
        return str(v)


# ─────────────────── LMS o'zgarishlarini kuzatish ───────────────────
# Har foydalanuvchi uchun bir marta yuboriladigan xabarlar chegarasi
_MAX_MSGS = 12


async def _collect_grade_changes(uid: int, c) -> list[str]:
    """Yangi baholar va yangi topshiriqlar."""
    old = await db.snapshot_get(uid, "grade")
    init = "__init__" in old
    cur: dict[str, str] = {"__init__": "1"}
    msgs: list[str] = []
    courses = await c.courses()
    for course in courses:
        tasks = await c.course_tasks(course.id, tz=TZ)
        for t in tasks:
            key = f"{course.id}:{t.name}"
            val = "" if t.score is None else _num(t.score)
            cur[key] = val
            if not init:
                continue
            ov = old.get(key)
            if ov is None and val == "":
                msgs.append(f"🆕 <b>Yangi topshiriq</b>\n📘 {esc(course.subject)} · "
                            f"{esc(t.lesson_type)}\n📝 {esc(t.name)}")
            elif val != "" and (ov is None or ov == "" or ov != val):
                mx = f"/{_num(t.max_score)}" if t.max_score is not None else ""
                verb = "yangilandi" if (ov and ov != "") else "qo'yildi"
                msgs.append(f"📊 <b>Baho {verb}!</b>\n📘 {esc(course.subject)}\n"
                            f"📝 {esc(t.name)} — <b>{val}{mx}</b>")
    await db.snapshot_set(uid, "grade", cur)
    return msgs


# NB chegaralari: sababsiz NB soni shu darajaga yetsa ogohlantiramiz
_NB_THRESHOLDS = [
    (5, "🚨 <b>CHETLATISH XAVFI!</b>"),
    (3, "⚠️ <b>Diqqat — NB ko'paymoqda</b>"),
]


async def _collect_attendance_changes(uid: int, c) -> list[str]:
    """Yangi qoldirilgan darslar (NB) + NB soni chegaraga yaqinlashsa ogohlantirish."""
    old = await db.snapshot_get(uid, "attendance")
    init = "__init__" in old
    cur: dict[str, str] = {"__init__": "1"}
    msgs: list[str] = []
    missed = await c.attendance()
    unexcused: dict[str, int] = {}
    for m in missed:
        key = f"{m.date}:{m.subject}:{m.lesson_type}:{m.theme_number}"
        val = "sababli" if m.excused else "sababsiz"
        cur[key] = val
        if not m.excused:
            unexcused[m.subject] = unexcused.get(m.subject, 0) + 1
        if init and key not in old:
            mark = "🟡" if m.excused else "🔴"
            msgs.append(f"{mark} <b>Yangi NB (qoldirilgan dars)</b>\n"
                        f"📘 {esc(m.subject)} · {esc(m.lesson_type)}\n"
                        f"📆 {esc(m.date)} · <i>{val}</i>")
    await db.snapshot_set(uid, "attendance", cur)

    # ── NB chegara ogohlantirishi ──
    warned = await db.snapshot_get(uid, "nbwarn")  # subject -> daraja
    warn_init = "__init__" in warned
    new_warn: dict[str, str] = {"__init__": "1"}
    for subj, cnt in unexcused.items():
        level = 0
        for th, _head in _NB_THRESHOLDS:
            if cnt >= th:
                level = th
                break
        new_warn[subj] = str(level)
        prev = int(warned.get(subj, "0") or 0)
        # faqat daraja OSHGANDA va birinchi tekshiruv bo'lmasa ogohlantiramiz
        if warn_init and level > prev:
            head = next(h for th, h in _NB_THRESHOLDS if th == level)
            msgs.append(f"{head}\n📘 {esc(subj)}\n"
                        f"🔴 Sababsiz NB: <b>{cnt}</b> ta\n"
                        "<i>Davomatga e'tibor bering — chetlatilmang!</i>")
    await db.snapshot_set(uid, "nbwarn", new_warn)
    return msgs


async def _collect_resource_changes(uid: int, c) -> list[str]:
    """Ustoz yuklagan yangi ma'ruza/amaliyot materiallari."""
    old = await db.snapshot_get(uid, "resource")
    init = "__init__" in old
    cur: dict[str, str] = {"__init__": "1"}
    msgs: list[str] = []
    courses = await c.courses()
    for course in courses:
        try:
            resources = await c.calendar_resources(course.id)
        except Exception:  # noqa: BLE001
            continue
        for r in resources:
            key = f"{course.id}:{r.url}"
            cur[key] = r.title or "material"
            if init and key not in old:
                kind = "📖 Ma'ruza" if r.kind == "lecture" else "✍️ Amaliyot"
                msgs.append(f"📦 <b>Yangi material</b>\n📘 {esc(course.subject)} · {kind}\n"
                            f"📄 {esc(r.title)}")
    await db.snapshot_set(uid, "resource", cur)
    return msgs


async def job_changes(bot: Bot):
    """LMS'da nimadir o'zgarsa (baho, NB, yangi material) — talabaga xabar beradi.
    Birinchi tekshiruv 'asos' sifatida saqlanadi (spam bo'lmasin)."""
    for u in await db.all_users(service="lms"):
        if not u.get("changes_on"):
            continue
        c = await _user_session(u["tg_id"])
        if not c:
            continue
        try:
            msgs: list[str] = []
            msgs += await _collect_grade_changes(u["tg_id"], c)
            msgs += await _collect_attendance_changes(u["tg_id"], c)
            msgs += await _collect_resource_changes(u["tg_id"], c)
            if not msgs:
                continue
            # ko'p bo'lsa — chegaralaymiz (flood bo'lmasin)
            shown = msgs[:_MAX_MSGS]
            for text in shown:
                try:
                    await bot.send_message(u["tg_id"], text)
                    await asyncio.sleep(0.3)
                except Exception as e:  # noqa: BLE001
                    log.info("changes send uid=%s: %s", u["tg_id"], e)
            if len(msgs) > _MAX_MSGS:
                await bot.send_message(
                    u["tg_id"], f"…va yana <b>{len(msgs) - _MAX_MSGS}</b> ta o'zgarish. "
                    "To'liq ko'rish uchun menyudan foydalaning.")
        except Exception as e:  # noqa: BLE001
            log.warning("changes uid=%s: %s", u["tg_id"], e)
        await asyncio.sleep(0.5)  # serverni bo'kib qo'ymaslik uchun


async def job_backup():
    """Kunlik DB zaxira — _backups/ ga nusxa, oxirgi 7 tasini saqlaydi."""
    import shutil
    import sqlite3
    from pathlib import Path
    src = Path(settings.db_file)
    if not src.exists():
        return
    bdir = src.parent / "_backups"
    bdir.mkdir(exist_ok=True)
    dst = bdir / f"tatu-{datetime.now(TZ).strftime('%Y-%m-%d')}.db"
    try:
        con = sqlite3.connect(str(src))
        try:
            con.execute("VACUUM INTO ?", (str(dst),))  # toza, izchil nusxa
        finally:
            con.close()
    except Exception:  # noqa: BLE001
        shutil.copy2(src, dst)  # zaxira usuli
    # eski zaxiralarni tozalash (oxirgi 7 ta qoladi)
    backups = sorted(bdir.glob("tatu-*.db"), reverse=True)
    for old in backups[7:]:
        try:
            old.unlink()
        except Exception:  # noqa: BLE001
            pass
    log.info("DB zaxira olindi: %s", dst.name)


async def job_cleanup():
    await session.cleanup_idle()


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    sch = AsyncIOScheduler(timezone=TZ)
    hh, mm = (settings.morning_push.split(":") + ["0"])[:2]
    sch.add_job(job_morning, "cron", hour=int(hh), minute=int(mm), args=[bot],
                id="morning", misfire_grace_time=3600)
    sch.add_job(job_deadlines, "interval", minutes=20, args=[bot],
                id="deadlines", misfire_grace_time=600)
    sch.add_job(job_autosubmit, "interval", minutes=2, args=[bot],
                id="autosubmit", misfire_grace_time=120)
    sch.add_job(job_changes, "interval", minutes=60, args=[bot],
                id="changes", misfire_grace_time=1800)
    sch.add_job(job_backup, "cron", hour=3, minute=30, id="backup",
                misfire_grace_time=7200)
    sch.add_job(job_cleanup, "interval", minutes=15, id="cleanup")
    sch.start()
    log.info("Scheduler ishga tushdi (morning=%s)", settings.morning_push)
    return sch
