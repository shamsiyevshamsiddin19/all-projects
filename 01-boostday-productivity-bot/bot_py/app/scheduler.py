"""Rejalashtirilgan vazifalar — cron.php ekvivalenti. Har daqiqada ishga tushiriladi."""

from __future__ import annotations

import calendar
import json
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

from . import db, push
from .config import settings
from .helpers import (
    build_todo_text,
    decode_task_groups,
    encode_task_groups,
    flatten_task_groups,
    now,
    todo_keyboard,
)
from .tg import send_challenge_post, send_message, send_plan_items

logger = logging.getLogger("boostday")
DT_FMT = "%Y-%m-%d %H:%M:%S"


def run_all() -> None:
    n = now()
    now_str = n.strftime(DT_FMT)
    today = n.strftime("%Y-%m-%d")
    logger.info("CRON_START now=%s tz=%s", now_str, settings.TIMEZONE)

    run_media_daily_plans(now_str)
    run_reminders(now_str)
    run_challenge_plans(today, now_str)
    run_daily_todo_posts(today, now_str)
    run_habit_reminders(n)
    run_group_reminders(n)
    run_habits_standalone_if_needed(n)
    run_calendar_posts(today, now_str)
    run_super_todo_alerts(now_str)
    run_daily_reports_if_needed(n)
    run_daily_todo_rollover_if_needed(n)
    run_weekly_reports_if_needed(n)
    run_monthly_reports_if_needed(n)
    run_yearly_reports_if_needed(n)

    logger.info("CRON_END")


def _parse(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, DT_FMT).replace(tzinfo=settings.tz)


def next_daily_run_after(time_str: str, reference: datetime | None = None) -> str:
    ref = reference or now()
    run = _parse(f"{ref.strftime('%Y-%m-%d')} {time_str}:00")
    if run <= ref:
        run += timedelta(days=1)
    return run.strftime(DT_FMT)


def daily_mode_should_send(mode: str | None, when: datetime) -> bool:
    mode = (mode or "everyday").lower()
    if mode not in ("odd", "even"):
        return True
    n = when.isoweekday()  # 1=Mon ... 7=Sun
    if n == 7:
        return False
    is_odd = (n % 2) == 1
    return is_odd if mode == "odd" else not is_odd


def sent_log_exists(plan_id: int, note: str) -> bool:
    return db.one("SELECT id FROM sent_logs WHERE plan_id = :p AND note = :n LIMIT 1",
                  {"p": plan_id, "n": note}) is not None


def add_sent_log(plan_id: int, sent_at: str, note: str) -> None:
    db.run("INSERT INTO sent_logs (plan_id, sent_at, note) VALUES (:p, :s, :n)",
           {"p": plan_id, "s": sent_at, "n": note})


def build_web_url(view: str, owner_id: int) -> str:
    base = (settings.WEB_APP_URL or "").strip()
    if base == "":
        return ""
    sep = "?" if "?" not in base else "&"
    return base + sep + urlencode({"view": view, "owner_id": owner_id})


def build_web_button(text: str, url: str) -> dict | None:
    if url == "":
        return None
    return {"inline_keyboard": [[{"text": text, "url": url}]]}


def send_user_message_by_id(user_id: int, text: str, reply_markup: dict | None = None) -> None:
    user = db.one("SELECT chat_id FROM users WHERE id = :id LIMIT 1", {"id": user_id})
    if not user or not user.get("chat_id"):
        return
    send_message(user["chat_id"], text, reply_markup)


def reset_task_statuses(tasks: list) -> list:
    for task in tasks:
        task["status"] = 0
        if "started_at" in task:
            task["started_at"] = None
        if "finished_at" in task:
            task["finished_at"] = None
        if "alerts" in task:
            task["alerts"] = []
    return tasks


def _load(js) -> list:
    try:
        v = json.loads(js or "null")
    except (ValueError, TypeError):
        return []
    return v if isinstance(v, list) else []


def run_media_daily_plans(now_str: str) -> None:
    plans = db.all_(
        "SELECT * FROM plans WHERE status = 'active' AND plan_type = 'daily_plan' "
        "AND next_run_at IS NOT NULL AND next_run_at <= :now", {"now": now_str})
    for plan in plans:
        send_plan_items(plan["channel_id"], _load(plan["items"]))
        db.run("UPDATE plans SET last_run = :n, next_run_at = :nra, updated_at = :n WHERE id = :id",
               {"n": now_str, "nra": next_daily_run_after(plan["time"], _parse(now_str)), "id": plan["id"]})
        add_sent_log(int(plan["id"]), now_str, "daily_plan")


def run_reminders(now_str: str) -> None:
    plans = db.all_(
        "SELECT * FROM plans WHERE status = 'active' AND plan_type = 'reminder' "
        "AND next_run_at IS NOT NULL AND next_run_at <= :now", {"now": now_str})
    for plan in plans:
        send_plan_items(plan["channel_id"], _load(plan["items"]))
        db.run("UPDATE plans SET status = 'done', last_run = :n, updated_at = :n WHERE id = :id",
               {"n": now_str, "id": plan["id"]})
        add_sent_log(int(plan["id"]), now_str, "reminder")


def run_challenge_plans(today: str, now_str: str) -> None:
    plans = db.all_(
        "SELECT p.*, u.birth_date FROM plans p JOIN users u ON u.id = p.owner_id "
        "WHERE p.status = 'active' AND p.plan_type = 'challenge' "
        "AND p.next_run_at IS NOT NULL AND p.next_run_at <= :now", {"now": now_str})
    for plan in plans:
        if not plan.get("start_date") or not plan.get("end_date") or not plan.get("time"):
            continue
        sd = str(plan["start_date"])
        ed = str(plan["end_date"])
        if today < sd:
            continue
        if today > ed:
            send_message(plan["channel_id"], "<b>Challenge yakunlandi</b>\n\nChallenge muddati tugadi.")
            db.run("UPDATE plans SET status = 'done', last_run = :n, updated_at = :n WHERE id = :id",
                   {"n": now_str, "id": plan["id"]})
            add_sent_log(int(plan["id"]), now_str, "challenge_finished")
            continue
        send_challenge_post(plan["channel_id"], plan, plan.get("birth_date"))
        db.run("UPDATE plans SET last_run = :n, next_run_at = :nra, updated_at = :n WHERE id = :id",
               {"n": now_str, "nra": next_daily_run_after(plan["time"], _parse(now_str)), "id": plan["id"]})
        add_sent_log(int(plan["id"]), now_str, "challenge")


def run_daily_todo_posts(today: str, now_str: str) -> None:
    plans = db.all_(
        "SELECT * FROM plans WHERE status = 'active' AND plan_type = 'daily_todo' "
        "AND next_run_at IS NOT NULL AND next_run_at <= :now", {"now": now_str})
    for plan in plans:
        week_mode = plan.get("week_mode") or "everyday"
        if not daily_mode_should_send(week_mode, _parse(now_str)):
            db.run("UPDATE plans SET next_run_at = :nra, updated_at = :n WHERE id = :id",
                   {"nra": next_daily_run_after(plan["time"], _parse(now_str)), "n": now_str, "id": plan["id"]})
            continue
        groups = decode_task_groups(plan["tasks"])
        last_run_date = str(plan["last_run"])[:10] if plan.get("last_run") else ""
        if last_run_date != today:
            reset_task_statuses(flatten_task_groups(groups))
        # Kunlik odatlar shu xabarga ALOHIDA bo'lim bo'lib qo'shiladi.
        from .webapp import habits_text_block
        body = build_todo_text(groups, "Har kungi rejalar") + habits_text_block(
            int(plan.get("owner_id") or 0), _parse(now_str))
        response = send_message(plan["channel_id"], body,
                                todo_keyboard(int(plan["id"]), groups, plan["plan_type"]))
        message_id = (response or {}).get("result", {}).get("message_id")
        db.run("UPDATE plans SET tasks = :t, message_id = :mid, last_run = :n, next_run_at = :nra, updated_at = :n WHERE id = :id",
               {"t": encode_task_groups(groups), "mid": message_id, "n": now_str,
                "nra": next_daily_run_after(plan["time"], _parse(now_str)), "id": plan["id"]})
        add_sent_log(int(plan["id"]), now_str, "daily_todo")


def run_group_reminders(n: datetime) -> None:
    """Reja BO'LIMI boshlanishidan oldin telefonga ogohlantirish.

    Vaqt bo'lim darajasida (`task_groups[].time`, masalan "18:00 - 19:30")
    saqlangani uchun eslatma ham bo'lim bo'yicha yuboriladi. Bo'limning
    BOSHLANISH vaqtidan 30/15/5/0 daqiqa oldin bitta xabar ketadi.

    Yubormaslik shartlari:
      · bo'limning barcha vazifalari allaqachon bajarilgan
      · o'sha bo'lim uchun o'sha offset allaqachon yuborilgan (`group_sent`)

    Odatlar (`run_habit_reminders`) bilan bir xil naqsh: avval telefon
    bildirishnomasi (push), yetib bormasa Telegram zaxira sifatida.
    """
    if not db.table_exists("plans"):
        return

    today = n.strftime("%Y-%m-%d")
    dow_ok_cache: dict[str, bool] = {}

    plans = db.all_(
        "SELECT id, owner_id, plan_type, week_mode, tasks, date, channel_name "
        "FROM plans WHERE status = 'active' AND plan_type IN ('daily_todo', 'todo')")

    for plan in plans:
        # Bir martalik TO-DO faqat o'z sanasida; har kungi reja — hafta rejimiga ko'ra
        if plan["plan_type"] == "todo":
            if str(plan.get("date") or "")[:10] != today:
                continue
        else:
            mode = plan.get("week_mode") or "everyday"
            if mode not in dow_ok_cache:
                dow_ok_cache[mode] = daily_mode_should_send(mode, n)
            if not dow_ok_cache[mode]:
                continue

        try:
            groups = decode_task_groups(plan["tasks"])
        except Exception:  # noqa: BLE001
            continue

        for gi, g in enumerate(groups):
            start = _group_start_time(g.get("time"))
            if not start:
                continue
            tasks = g.get("tasks") or []
            if not tasks:
                continue
            # Hammasi bajarilgan bo'lsa bezovta qilmaymiz
            if all(int(t.get("status", 0) or 0) == 1 for t in tasks):
                continue

            try:
                hh, mm = start.split(":")
                target = n.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            except (ValueError, TypeError):
                continue

            left = int((target - n).total_seconds() // 60)
            if left not in (30, 15, 5, 0):
                continue

            pid = int(plan["id"])
            already = db.one(
                "SELECT id FROM group_sent WHERE plan_id=:p AND group_index=:g "
                "AND sent_date=:d AND offset_min=:o",
                {"p": pid, "g": gi, "d": today, "o": left})
            if already:
                continue

            name = (g.get("name") or "").strip() or "Reja"
            left_n = len([t for t in tasks if int(t.get("status", 0) or 0) != 1])
            if left == 0:
                title = f"⏰ {name}"
                when = "Boshlandi!"
            else:
                title = f"🔔 {name}"
                when = f"{left} daqiqa qoldi · {g.get('time')}"
            body = f"{when}\n{left_n} ta vazifa"

            try:
                sent = push.send(int(plan.get("owner_id") or 0), title, body,
                                 url="/#/kun", tag=f"group-{pid}-{gi}")
                if sent == 0:
                    send_user_message_by_id(
                        int(plan.get("owner_id") or 0),
                        f"<b>{title}</b>\n{body}" + (
                            "\n\n<i>Bildirishnoma ulanmagan — Sozlamalardan yoqing.</i>"
                            if left == 0 else ""))
                db.run("INSERT INTO group_sent (plan_id, group_index, sent_date, offset_min) "
                       "VALUES (:p,:g,:d,:o) ON CONFLICT DO NOTHING",
                       {"p": pid, "g": gi, "d": today, "o": left})
            except Exception:  # noqa: BLE001 — bittasi yiqilsa qolgani ketaversin
                logger.exception("GROUP_REMINDER xato plan_id=%s group=%s", pid, gi)


def _group_start_time(raw) -> str:
    """"18:00 - 19:30" yoki "18:00" -> "18:00". Mos kelmasa ''."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})", str(raw or ""))
    if not m:
        return ""
    hh, mm = int(m.group(1)), int(m.group(2))
    if hh > 23 or mm > 59:
        return ""
    return f"{hh:02d}:{mm:02d}"


def run_habit_reminders(n: datetime) -> None:
    """Kunlik odatlar uchun oldindan ogohlantirish.

    Har odatda `remind` maydonida daqiqalar ro'yxati bo'ladi (masalan
    `60,30,15,5`). Cron har DAQIQADA ishlagani uchun aniq mos kelgan
    daqiqada bitta xabar yuboriladi; `habit_sent` jadvali takror
    yuborilishining oldini oladi (UNIQUE cheklov bilan).

    `offset_min = 0` — "vaqti bo'ldi" xabari.
    Allaqachon bajarilgan (belgilangan) odat uchun eslatma YUBORILMAYDI.
    """
    from .webapp import habit_mode_matches      # aylanma importdan qochish

    if not db.table_exists("habits"):
        return
    today = n.strftime("%Y-%m-%d")
    rows = db.all_(
        "SELECT id, owner_id, name, at_time, week_mode, remind, note "
        "FROM habits WHERE is_deleted = 0 AND is_active = 1")
    if not rows:
        return

    done = {int(r["habit_id"]) for r in
            db.all_("SELECT habit_id FROM habit_log WHERE done_date = :d", {"d": today})}

    for h in rows:
        hid = int(h["id"])
        if hid in done:
            continue
        if not habit_mode_matches(h["week_mode"], n):
            continue

        try:
            hh, mm = str(h["at_time"]).split(":")
            target = n.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        except (ValueError, TypeError):
            continue

        # Necha daqiqa qoldi (manfiy bo'lsa vaqt o'tib ketgan)
        left = int((target - n).total_seconds() // 60)
        offsets = [0]
        for part in str(h["remind"] or "").split(","):
            part = part.strip()
            if part.isdigit():
                offsets.append(int(part))
        if left not in offsets:
            continue

        # Takror yuborilmasin
        already = db.one(
            "SELECT id FROM habit_sent WHERE habit_id=:h AND sent_date=:d AND offset_min=:o",
            {"h": hid, "d": today, "o": left})
        if already:
            continue

        if left == 0:
            title = f"⏰ {h['name']}"
            when = "Vaqti bo'ldi!"
        elif left >= 60:
            hours = left // 60
            rest = left % 60
            qoldi = f"{hours} soat" + (f" {rest} daqiqa" if rest else "")
            title = f"🔔 {h['name']}"
            when = f"{qoldi} qoldi · {h['at_time']}"
        else:
            title = f"🔔 {h['name']}"
            when = f"{left} daqiqa qoldi · {h['at_time']}"

        body = when
        if h.get("note"):
            body += f"\n{h['note']}"

        try:
            # Avval TELEFON BILDIRISHNOMASI (Instagram/YouTube kabi).
            # Telegram — faqat zaxira: obuna bo'lmasa yoki push yetib
            # bormasa foydalanuvchi eslatmasiz qolmasin.
            n = push.send(int(h["owner_id"]), title, body,
                          url="/#habits", tag=f"habit-{hid}")
            if n == 0:
                send_user_message_by_id(
                    int(h["owner_id"]),
                    f"<b>{title}</b>\n{body}" + (
                        "\n\n<i>Bildirishnoma ulanmagan — Sozlamalardan yoqing.</i>"
                        if left == 0 else ""))
            db.run("INSERT INTO habit_sent (habit_id, sent_date, offset_min) "
                   "VALUES (:h,:d,:o) ON CONFLICT DO NOTHING",
                   {"h": hid, "d": today, "o": left})
        except Exception:  # noqa: BLE001 — bitta odat yiqilsa qolgani yuborilaversin
            logger.exception("HABIT_REMINDER xato habit_id=%s", hid)


def run_habits_standalone_if_needed(n: datetime) -> None:
    """Ertaga reja bo'lmasa — odatlar ro'yxati O'ZI yuboriladi.

    Odatda odatlar Boostday'ning kunlik xabariga qo'shiladi
    (`run_daily_todo_posts` -> `habits_text_block`). Ammo o'sha kuni
    birorta ham `daily_todo` reja yuborilmasa, foydalanuvchi kunlik
    odatlar ro'yxatini umuman ko'rmay qolardi — shuning uchun kunning
    BELGILANGAN vaqtida alohida xabar ketadi.
    """
    from .webapp import habits_text_block

    if not db.table_exists("habits"):
        return
    # Kuniga bir marta, ertalab 08:00 da
    if n.hour != 8 or n.minute != 0:
        return
    today = n.strftime("%Y-%m-%d")

    owners = db.all_("SELECT DISTINCT owner_id FROM habits WHERE is_deleted=0 AND is_active=1")
    for row in owners:
        oid = int(row["owner_id"])
        # Bugun shu egaga daily_todo yuborilganmi?
        posted = db.one(
            "SELECT s.id FROM sent_logs s JOIN plans p ON p.id = s.plan_id "
            "WHERE p.owner_id = :u AND p.plan_type = 'daily_todo' AND s.note = 'daily_todo' "
            "AND s.sent_at >= :d LIMIT 1",
            {"u": oid, "d": today + " 00:00:00"})
        if posted:
            continue      # reja ketgan — odatlar o'sha xabarda bor

        block = habits_text_block(oid, n)
        if not block:
            continue
        already = db.one(
            "SELECT id FROM habit_sent WHERE habit_id = 0 AND sent_date = :d AND offset_min = :o",
            {"d": today, "o": -1})
        if already:
            continue
        try:
            send_user_message_by_id(oid, "📋 <b>Bugungi ro'yxat</b>" + block)
            db.run("INSERT INTO habit_sent (habit_id, sent_date, offset_min) "
                   "VALUES (0,:d,-1) ON CONFLICT DO NOTHING", {"d": today})
        except Exception:  # noqa: BLE001
            logger.exception("HABITS_STANDALONE xato owner_id=%s", oid)


def run_calendar_posts(today: str, now_str: str) -> None:
    plans = db.all_(
        "SELECT * FROM plans WHERE status = 'active' AND plan_type IN ('todo', 'super_todo') "
        "AND date = :today AND next_run_at IS NOT NULL AND next_run_at <= :now "
        "AND (message_id IS NULL OR message_id = 0)", {"today": today, "now": now_str})
    for plan in plans:
        groups = decode_task_groups(plan["tasks"])
        title = "Super TO-DO" if plan["plan_type"] == "super_todo" else "TO-DO"
        response = send_message(plan["channel_id"], build_todo_text(groups, title),
                                todo_keyboard(int(plan["id"]), groups, plan["plan_type"]))
        message_id = (response or {}).get("result", {}).get("message_id")
        db.run("UPDATE plans SET message_id = :mid, last_run = :n, updated_at = :n WHERE id = :id",
               {"mid": message_id, "n": now_str, "id": plan["id"]})
        add_sent_log(int(plan["id"]), now_str, plan["plan_type"])


def run_super_todo_alerts(now_str: str) -> None:
    plans = db.all_(
        "SELECT * FROM plans WHERE status = 'active' AND plan_type = 'super_todo' "
        "AND date = :today AND message_id IS NOT NULL", {"today": now().strftime("%Y-%m-%d")})
    now_ts = _parse(now_str)
    for plan in plans:
        groups = decode_task_groups(plan["tasks"])
        tasks = flatten_task_groups(groups)
        changed = False
        for task in tasks:
            status = int(task.get("status", 0) or 0)
            if status != 2 or not task.get("started_at") or not task.get("duration"):
                continue
            started = _parse(task["started_at"])
            duration_min = int(task["duration"])
            end = started + timedelta(minutes=duration_min)
            total_sec = max(1, duration_min * 60)
            passed_sec = max(0, (now_ts - started).total_seconds())
            percent = (passed_sec / total_sec) * 100
            alerts = task.get("alerts") if isinstance(task.get("alerts"), list) else []

            if percent >= 50 and "50" not in alerts:
                send_message(plan["channel_id"], f"<b>Super TO-DO ogohlantirish</b>\n\n<b>{task['text']}</b> vazifasining 50% vaqti o'tdi.")
                alerts.append("50")
                changed = True
            if percent >= 75 and "75" not in alerts:
                send_message(plan["channel_id"], f"<b>Super TO-DO ogohlantirish</b>\n\n<b>{task['text']}</b> vazifasining 75% vaqti o'tdi.")
                alerts.append("75")
                changed = True
            if (end - now_ts).total_seconds() <= 60 and "1m" not in alerts:
                send_message(plan["channel_id"], f"<b>Super TO-DO ogohlantirish</b>\n\n<b>{task['text']}</b> tugashiga 1 daqiqa qoldi.")
                alerts.append("1m")
                changed = True
            if now_ts >= end and "done_time" not in alerts:
                send_message(plan["channel_id"], f"<b>Super TO-DO</b>\n\n<b>{task['text']}</b> uchun belgilangan vaqt tugadi.")
                alerts.append("done_time")
                changed = True
            task["alerts"] = alerts
        if changed:
            db.run("UPDATE plans SET tasks = :t, updated_at = :n WHERE id = :id",
                   {"t": encode_task_groups(groups), "n": now_str, "id": plan["id"]})


def run_daily_reports_if_needed(n: datetime) -> None:
    """Har kuni 23:59 da bugungi TO-DO/Super TO-DO uchun qisqa hisobot.

    ESLATMA (foydalanuvchi so'rovi bilan o'chirilgan xatti-harakat):
    ilgari shu yerda bajarilmagan vazifalar "-> " prefiksi bilan ERTANGI
    kunga YANGI reja qilib avtomatik ko'chirilardi — ya'ni kecha
    qilinmagan TO-DO ishlar bugun QAYTA paydo bo'lardi. Foydalanuvchi
    buni aniq xohlamadi ("kecha qilinmagan vazifalar bugunga yana
    kelyapti — kelmaydigan qil"), shuning uchun ko'chirish butunlay olib
    tashlandi: TO-DO faqat O'Z sanasida yashaydi, o'sha kun tugasa
    bajarilmagan qismi shunchaki tarixda "bajarilmagan" bo'lib qoladi.
    Hisobot xabari (statistika) esa saqlanib qoldi — bu foydali va
    shikoyat qilinmagan.
    """
    if n.strftime("%H:%M") != "23:59":
        return
    today = n.strftime("%Y-%m-%d")
    plans = db.all_(
        "SELECT * FROM plans WHERE status = 'active' AND plan_type IN ('todo', 'super_todo') "
        "AND date = :today AND report_sent = 0", {"today": today})
    for plan in plans:
        groups = decode_task_groups(plan["tasks"])
        tasks = flatten_task_groups(groups)
        total = len(tasks)
        completed = sum(1 for t in tasks if int(t.get("status", 0) or 0) == 1)
        percent = round((completed / total) * 100, 1) if total > 0 else 0
        report = ("<b>Kunlik hisobot</b>\n\n"
                  f"Sana: <code>{today}</code>\nJami vazifalar: <b>{total}</b>\n"
                  f"Bajarilgan: <b>{completed}</b>\nQolgan: <b>{total - completed}</b>\n"
                  f"Natija: <b>{percent}%</b>")
        send_message(plan["channel_id"], report)
        upsert_history(int(plan["owner_id"]), str(plan["channel_id"]), today, total, completed)

        db.run("UPDATE plans SET report_sent = 1, updated_at = :n WHERE id = :id",
               {"n": n.strftime(DT_FMT), "id": plan["id"]})
        add_sent_log(int(plan["id"]), n.strftime(DT_FMT), "daily_report")


def run_daily_todo_rollover_if_needed(n: datetime) -> None:
    if n.strftime("%H:%M") != "23:59":
        return
    today = n.strftime("%Y-%m-%d")
    plans = db.all_("SELECT * FROM plans WHERE status = 'active' AND plan_type = 'daily_todo'")
    for plan in plans:
        note = f"daily_todo_rollover:{today}"
        if sent_log_exists(int(plan["id"]), note):
            continue
        groups = decode_task_groups(plan["tasks"])
        tasks = flatten_task_groups(groups)
        total = len(tasks)
        completed = sum(1 for t in tasks if int(t.get("status", 0) or 0) == 1)
        upsert_history(int(plan["owner_id"]), str(plan["channel_id"]), today, total, completed)
        reset_task_statuses(tasks)
        db.run("UPDATE plans SET tasks = :t, message_id = NULL, updated_at = :n WHERE id = :id",
               {"t": encode_task_groups(groups), "n": n.strftime(DT_FMT), "id": plan["id"]})
        add_sent_log(int(plan["id"]), n.strftime(DT_FMT), note)


def _monday_this_week(n: datetime) -> datetime:
    return (n - timedelta(days=n.isoweekday() - 1)).replace(hour=0, minute=0, second=0, microsecond=0)


def run_weekly_reports_if_needed(n: datetime) -> None:
    if n.strftime("%H:%M") != "23:59" or n.isoweekday() != 7:
        return
    start = _monday_this_week(n)
    end = start + timedelta(days=6)
    send_period_report_to_users("weekly", start, end, n)


def run_monthly_reports_if_needed(n: datetime) -> None:
    if n.strftime("%H:%M") != "23:59":
        return
    last_day = calendar.monthrange(n.year, n.month)[1]
    if n.day != last_day:
        return
    start = n.replace(day=1)
    end = n.replace(day=last_day)
    send_period_report_to_users("monthly", start, end, n)


def run_yearly_reports_if_needed(n: datetime) -> None:
    if n.strftime("%H:%M") != "23:59" or n.strftime("%m-%d") != "12-31":
        return
    start = n.replace(month=1, day=1)
    end = n.replace(month=12, day=31)
    send_period_report_to_users("yearly", start, end, n)


def history_user_ids_in_range(start_date: str, end_date: str) -> list[int]:
    rows = db.all_(
        "SELECT DISTINCT user_id FROM history "
        "WHERE CONCAT(LPAD(year, 4, '0'), '-', LPAD(month, 2, '0'), '-', LPAD(day, 2, '0')) BETWEEN :s AND :e "
        "ORDER BY user_id", {"s": start_date, "e": end_date})
    return [int(r["user_id"]) for r in rows]


def history_summary_for_range(user_id: int, start_date: str, end_date: str) -> dict:
    row = db.one(
        "SELECT COUNT(*) AS day_count, COALESCE(SUM(total_tasks), 0) AS total_tasks_sum, "
        "COALESCE(SUM(completed_tasks), 0) AS completed_tasks_sum FROM history "
        "WHERE user_id = :u AND CONCAT(LPAD(year, 4, '0'), '-', LPAD(month, 2, '0'), '-', LPAD(day, 2, '0')) BETWEEN :s AND :e",
        {"u": user_id, "s": start_date, "e": end_date}) or {}
    total = int(row.get("total_tasks_sum") or 0)
    completed = int(row.get("completed_tasks_sum") or 0)
    return {
        "days": int(row.get("day_count") or 0),
        "total_tasks": total,
        "completed_tasks": completed,
        "percent": round((completed / total) * 100, 1) if total > 0 else 0,
    }


def report_title_and_period(kind: str, start: datetime, end: datetime) -> tuple[str, str]:
    if kind == "weekly":
        return "Haftalik statistika", f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"
    if kind == "monthly":
        return "Oylik statistika", start.strftime("%Y-%m")
    return "Yillik statistika", start.strftime("%Y")


def send_period_report_to_users(kind: str, start: datetime, end: datetime, n: datetime) -> None:
    user_ids = history_user_ids_in_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    title, period_text = report_title_and_period(kind, start, end)
    for user_id in user_ids:
        note = f"{kind}_report:{period_text}:{user_id}"
        if sent_log_exists(0, note):
            continue
        summary = history_summary_for_range(user_id, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        if summary["total_tasks"] <= 0:
            continue
        text = (f"<b>{title}</b>\n\nDavr: <code>{period_text}</code>\n"
                f"Faol kunlar: <b>{summary['days']}</b>\nJami vazifalar: <b>{summary['total_tasks']}</b>\n"
                f"Bajarilgan: <b>{summary['completed_tasks']}</b>\n"
                f"Bajarilmagan: <b>{summary['total_tasks'] - summary['completed_tasks']}</b>\n"
                f"Natija: <b>{summary['percent']}%</b>")
        url = build_web_url("stats", user_id)
        keyboard = build_web_button("Batafsil statistikani ko'rish", url)
        send_user_message_by_id(user_id, text, keyboard)
        add_sent_log(0, n.strftime(DT_FMT), note)


def upsert_history(user_id: int, channel_id: str, date: str, total: int, completed: int) -> None:
    if user_id <= 0:
        return
    parts = date.split("-")
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    ts = now().strftime(DT_FMT)
    row = db.one("SELECT * FROM history WHERE user_id = :u AND year = :y AND month = :m AND day = :d",
                 {"u": user_id, "y": year, "m": month, "d": day})
    if row:
        db.run(
            "UPDATE history SET total_tasks = :t, completed_tasks = :c, last_channel_id = :ch, updated_at = :n WHERE id = :id",
            {"t": int(row["total_tasks"]) + total, "c": int(row["completed_tasks"]) + completed,
             "ch": channel_id, "n": ts, "id": row["id"]})
        return
    db.run(
        "INSERT INTO history (user_id, year, month, day, total_tasks, completed_tasks, last_channel_id, created_at, updated_at) "
        "VALUES (:u, :y, :m, :d, :t, :c, :ch, :n, :n)",
        {"u": user_id, "y": year, "m": month, "d": day, "t": total, "c": completed, "ch": channel_id, "n": ts})
