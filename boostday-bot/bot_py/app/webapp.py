"""Web mini-app JSON API — `/boost/api?action=...` dispatch qiladi."""

from __future__ import annotations

import calendar
import json
import logging
import re
from datetime import datetime, timedelta

from . import db
from . import push as push_mod
from .config import settings
from .helpers import decode_task_groups, encode_task_groups, flatten_task_groups, now

logger = logging.getLogger("boostday")

DT_FMT = "%Y-%m-%d %H:%M:%S"
ALLOWED_TYPES = ["daily_plan", "challenge", "reminder", "todo", "super_todo", "daily_todo"]


class JsonResult(Exception):
    """jsonResponse() — natijani darhol qaytaradi (early return)."""

    def __init__(self, ok: bool, message: str, extra: dict | None = None):
        self.payload = {"ok": ok, "message": message, **(extra or {})}


def _now_str() -> str:
    return now().strftime(DT_FMT)


def _decode(value) -> list:
    if not value:
        return []
    try:
        v = json.loads(value)
    except (ValueError, TypeError):
        return []
    return v if isinstance(v, list) else []


def _valid_date(date: str) -> bool:
    if not date:
        return False
    try:
        return datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d") == date
    except (ValueError, TypeError):
        return False


def _valid_time(t: str) -> bool:
    return re.match(r"^(2[0-3]|[01]?\d):([0-5]\d)$", t or "") is not None


def _build_preview(items: list, tasks: list) -> str:
    for item in items:
        if item.get("text"):
            return str(item["text"])[:120]
        if item.get("caption"):
            return str(item["caption"])[:120]
    task_texts = [str(t["text"]) for t in tasks if t.get("text")]
    return ", ".join(task_texts)[:120]


def _resolve_channel_name(channel_id: str, channel_name: str) -> str:
    if channel_name != "" or channel_id == "" or not db.table_exists("user_channels"):
        return channel_name
    row = db.one("SELECT channel_name FROM user_channels WHERE channel_id = :c ORDER BY id DESC LIMIT 1",
                 {"c": channel_id})
    return str(row["channel_name"]) if row and row.get("channel_name") else ""


def _normalize_plan_row(row: dict) -> dict:
    items = _decode(row.get("items"))
    task_groups = decode_task_groups(row.get("tasks"))
    tasks = flatten_task_groups(task_groups)
    channel_id = str(row.get("channel_id") or "")
    channel_name = _resolve_channel_name(channel_id, str(row.get("channel_name") or ""))
    week_mode = row.get("week_mode")
    return {
        "id": int(row.get("id") or 0),
        "owner_id": int(row.get("owner_id") or 0),
        "channel_id": channel_id,
        "channel_name": channel_name,
        "plan_type": str(row.get("plan_type") or ""),
        "items": items,
        "tasks": tasks,
        "task_groups": task_groups,
        "time": str(row.get("time") or ""),
        "date": str(row.get("date") or ""),
        "start_date": str(row.get("start_date") or ""),
        "end_date": str(row.get("end_date") or ""),
        "status": str(row.get("status") or "active"),
        "week_mode": str(week_mode) if week_mode not in (None, "") else "everyday",
        "next_run_at": str(row.get("next_run_at") or ""),
        "last_run": str(row.get("last_run") or ""),
        "message_id": int(row.get("message_id") or 0),
        "preview": _build_preview(items, tasks),
    }


def list_channels(owner_id: int = 0) -> list:
    if not db.table_exists("user_channels"):
        return []
    if owner_id > 0:
        return db.all_("SELECT id, user_id, channel_id, channel_name, channel_username, topics FROM user_channels "
                       "WHERE user_id = :u ORDER BY id DESC", {"u": owner_id})
    return db.all_("SELECT id, user_id, channel_id, channel_name, channel_username, topics FROM user_channels ORDER BY id DESC")


# Sport/Til/Dasturlash bo'limidan mashq yuborilganda avtomatik tanlash uchun
# ruxsat etilgan mavzular. Frontend'dagi TOPICS (assets/js/app2/boost.js) bilan
# AYNAN bir xil bo'lishi shart — aks holda saytda belgilangan mavzu shu yerda
# jimgina olib tashlanadi ("Saqlandi" chiqadi, lekin hech narsa yozilmaydi).
# ⚠️ Saytdagi `assets/js/app2/boost.js::TOPICS` bilan BIR XIL bo'lishi shart —
# bu qat'iy whitelist, ro'yxatda yo'q mavzu jimgina tashlab yuboriladi.
CHANNEL_TOPICS = {"sport", "english", "russian", "dasturlash", "kun"}


def _clean_topics(raw: str) -> str:
    """Vergul bilan ajratilgan mavzular satrini tekshirib, ruxsat etilganlarini qaytaradi."""
    seen, clean = set(), []
    for t in (raw or "").split(","):
        t = t.strip().lower()
        if t in CHANNEL_TOPICS and t not in seen:
            seen.add(t)
            clean.append(t)
    return ",".join(clean)


def list_plans(owner_id: int = 0) -> list:
    if not db.table_exists("plans"):
        return []
    if owner_id > 0:
        rows = db.all_("SELECT * FROM plans WHERE owner_id = :u ORDER BY id DESC", {"u": owner_id})
    else:
        rows = db.all_("SELECT * FROM plans ORDER BY id DESC")
    result = []
    for row in rows:
        norm = _normalize_plan_row(row)
        if norm["status"] == "deleted" or norm["plan_type"] == "":
            continue
        result.append(norm)
    return result


def get_plan(plan_id: int, owner_id: int = 0) -> dict | None:
    if not db.table_exists("plans"):
        return None
    if owner_id > 0:
        row = db.one("SELECT * FROM plans WHERE id = :id AND owner_id = :u LIMIT 1", {"id": plan_id, "u": owner_id})
    else:
        row = db.one("SELECT * FROM plans WHERE id = :id LIMIT 1", {"id": plan_id})
    return _normalize_plan_row(row) if row else None


def _normalize_week_mode(payload: dict) -> str:
    if payload.get("plan_type") != "daily_todo":
        return "everyday"
    mode = str(payload.get("week_mode") or "everyday").strip().lower()
    return mode if mode in ("everyday", "odd", "even") else "everyday"


def _next_daily_dt(time_str: str) -> str:
    n = now()
    run = datetime.strptime(f"{n.strftime('%Y-%m-%d')} {time_str}:00", DT_FMT).replace(tzinfo=settings.tz)
    if run <= n:
        run += timedelta(days=1)
    return run.strftime(DT_FMT)


def _next_run_at(payload: dict) -> str | None:
    pt = payload["plan_type"]
    if pt in ("daily_plan", "daily_todo"):
        return _next_daily_dt(payload["time"])
    if pt == "reminder":
        return f"{payload['date']} {payload['time']}:00"
    if pt == "challenge":
        base = max(now().strftime("%Y-%m-%d"), payload["start_date"])
        return f"{base} {payload['time']}:00"
    if pt in ("todo", "super_todo"):
        return f"{payload['date']} {payload['time']}:00"
    return None


def _detect_owner_id(channel_id: str, fallback: int = 0) -> int:
    if not db.table_exists("user_channels"):
        return fallback
    row = db.one("SELECT user_id FROM user_channels WHERE channel_id = :c ORDER BY id DESC LIMIT 1", {"c": channel_id})
    return int(row["user_id"]) if row and row.get("user_id") is not None else fallback


def validate_payload(payload: dict) -> None:
    if payload["channel_id"] == "":
        raise JsonResult(False, "Kanal tanlanmagan")
    if payload["plan_type"] == "":
        raise JsonResult(False, "Yozuv turi tanlanmagan")
    if payload["time"] == "" or not _valid_time(payload["time"]):
        raise JsonResult(False, "Vaqt formati noto'g'ri")
    if payload["plan_type"] not in ALLOWED_TYPES:
        raise JsonResult(False, "Noto'g'ri yozuv turi")
    if payload["plan_type"] == "reminder":
        if not _valid_date(payload["date"]):
            raise JsonResult(False, "Eslatma sanasi kerak")
    if payload["plan_type"] == "challenge":
        if not _valid_date(payload["start_date"]) or not _valid_date(payload["end_date"]):
            raise JsonResult(False, "Challenge sanalari kerak")
        if payload["start_date"] > payload["end_date"]:
            raise JsonResult(False, "Challenge tugash sanasi boshlanish sanasidan kichik bo'lishi mumkin emas")
    if payload["plan_type"] in ("todo", "super_todo"):
        if not _valid_date(payload["date"]):
            raise JsonResult(False, "TO-DO sanasi kerak")
        if not flatten_task_groups(payload["tasks"]):
            raise JsonResult(False, "Kamida bitta task kerak")
        return
    if payload["plan_type"] == "daily_todo":
        if not flatten_task_groups(payload["tasks"]):
            raise JsonResult(False, "Har kungi reja uchun kamida bitta task kerak")
        return
    if not payload["items"]:
        raise JsonResult(False, "Kamida bitta kontent kerak")


def save_plan(payload: dict) -> int:
    if not db.table_exists("plans"):
        raise JsonResult(False, "plans jadvali topilmadi")

    columns = db.table_columns("plans")
    # Egа — autentifikatsiya qilingan owner_id (client soxta yubora olmaydi; main.py o'rnatadi).
    owner_id = int(payload.get("owner_id") or 0)
    ts = _now_str()

    data = {
        "owner_id": owner_id,
        "channel_id": payload["channel_id"],
        "channel_name": payload["channel_name"],
        "plan_type": payload["plan_type"],
        "items": json.dumps(payload["items"], ensure_ascii=False),
        "tasks": encode_task_groups(payload["tasks"]),
        "time": payload["time"],
        "date": payload["date"] or None,
        "start_date": payload["start_date"] or None,
        "end_date": payload["end_date"] or None,
        "week_mode": _normalize_week_mode(payload),
        "next_run_at": _next_run_at(payload),
        "status": "active",
        "report_sent": 0,
        "updated_at": ts,
        "created_at": ts,
    }
    filtered = {k: v for k, v in data.items() if k in columns}

    if payload["id"] > 0:
        existing = get_plan(int(payload["id"]), int(payload["owner_id"]) if payload.get("owner_id") else 0)
        if not existing:
            raise JsonResult(False, "Yozuv topilmadi")
        sets = {k: v for k, v in filtered.items() if k != "created_at"}
        set_clause = ", ".join(f"{k} = :{k}" for k in sets)
        sql = f"UPDATE plans SET {set_clause} WHERE id = :_id"
        params = dict(sets)
        params["_id"] = payload["id"]
        if payload.get("owner_id"):
            sql += " AND owner_id = :_owner"
            params["_owner"] = int(payload["owner_id"])
        db.run(sql, params)
        return int(payload["id"])

    cols = list(filtered.keys())
    placeholders = ", ".join(f":{c}" for c in cols)
    sql = f"INSERT INTO plans ({', '.join(cols)}) VALUES ({placeholders})"
    return db.run_returning_id(sql, filtered)


def refresh_telegram_message(plan_id: int) -> None:
    """Saytdan o'zgartirilgan rejaning Telegramdagi xabarini yangilaydi.

    Bot vazifa ro'yxatini kanalga tugmalar bilan yuboradi va `message_id` ni
    saqlaydi. Saytdan belgilash faqat bazani o'zgartirsa, Telegramdagi eski
    tugmalar belgilanmagan holicha qolib ketardi (ikki joyda ikki xil holat).
    Shuning uchun saqlashdan keyin o'sha xabarni qayta chizamiz.

    Xato bo'lsa (xabar o'chirilgan, juda eski, bot chiqarilgan) — jim o'tamiz:
    saqlashning o'zi muvaffaqiyatli bo'lgan, uni bekor qilish noto'g'ri bo'lardi.
    """
    from .helpers import build_todo_text, decode_task_groups, todo_keyboard
    from .tg import edit_message

    try:
        plan = db.one("SELECT * FROM plans WHERE id = :id", {"id": int(plan_id)})
        if not plan:
            return
        message_id = int(plan.get("message_id") or 0)
        if message_id <= 0:
            return                      # hali yuborilmagan — yangilanadigan xabar yo'q
        if plan.get("plan_type") not in ("todo", "super_todo", "daily_todo"):
            return                      # tugmali ro'yxat faqat shu turlarda

        groups = decode_task_groups(plan["tasks"])
        title = {
            "super_todo": "⏱ Super TO-DO",
            "daily_todo": "Har kungi rejalar",
        }.get(plan["plan_type"], "🗓 TO-DO")
        edit_message(plan["channel_id"], message_id,
                     build_todo_text(groups, title),
                     todo_keyboard(int(plan["id"]), groups, plan["plan_type"]))
    except Exception:  # noqa: BLE001
        logger.exception("Telegram xabarini yangilab bo'lmadi (plan_id=%s)", plan_id)


def channel_belongs_to(channel_id: str, owner_id: int) -> bool:
    if owner_id <= 0 or not db.table_exists("user_channels"):
        return False
    row = db.one("SELECT id FROM user_channels WHERE user_id = :u AND channel_id = :c LIMIT 1",
                 {"u": owner_id, "c": channel_id})
    return bool(row)


def _release_topics_from_others(owner_id: int, topics: list[str], keep_channel_row_id: int = 0) -> None:
    """Har mavzu faqat BITTA kanalga tegishli bo'lishi kerak — yangi kanalga
    biriktirilganda, o'sha mavzu(lar) boshqa kanallardagi ro'yxatdan olib
    tashlanadi (kanal o'zi butunlay o'chirilmaydi, faqat shu mavzu(lar) chiqadi)."""
    if not topics:
        return
    others = db.all_("SELECT id, topics FROM user_channels WHERE user_id = :u AND topics != '' AND id != :id",
                     {"u": owner_id, "id": keep_channel_row_id})
    for row in others:
        cur = [t.strip() for t in str(row["topics"] or "").split(",") if t.strip()]
        new = [t for t in cur if t not in topics]
        if new != cur:
            db.run("UPDATE user_channels SET topics = :t WHERE id = :id", {"t": ",".join(new), "id": row["id"]})


def add_channel_for_owner(owner_id: int, raw: str, topics: str = "") -> dict:
    """Mini app orqali kanal/guruh ulaydi. Bot admin bo'lishi shart. Natija dict qaytaradi."""
    from .helpers import normalize_channel_candidates, now_str
    from .tg import bot_is_admin, get_chat_info_multi, is_supported_target_chat, target_chat_type_label

    if owner_id <= 0:
        raise JsonResult(False, "Avtorizatsiya kerak")
    raw = (raw or "").strip()
    clean_topics = _clean_topics(topics)
    candidates = normalize_channel_candidates(raw)
    if not candidates:
        raise JsonResult(False, "Format noto'g'ri. Masalan: @kanal_nomi yoki -100... ID")

    chat = get_chat_info_multi(candidates)
    if not chat:
        raise JsonResult(False, "Kanal/guruh topilmadi. Avval botni admin qiling.")
    if not is_supported_target_chat(chat):
        raise JsonResult(False, f"Faqat kanal yoki guruh ulanadi (topildi: {target_chat_type_label(chat)})")

    channel_id = str(chat["id"])
    channel_name = chat.get("title") or candidates[0]
    channel_username = ("@" + chat["username"]) if chat.get("username") else None

    if not bot_is_admin(channel_id):
        raise JsonResult(False, "Bot bu kanal/guruhda admin emas. Avval administrator qiling.")

    existing = db.one("SELECT id FROM user_channels WHERE user_id = :u AND channel_id = :c",
                      {"u": owner_id, "c": channel_id})
    if clean_topics:
        _release_topics_from_others(owner_id, clean_topics.split(","), existing["id"] if existing else 0)

    ts = now_str()
    if existing:
        db.run("UPDATE user_channels SET channel_name = :n, channel_username = :un, topics = :t WHERE id = :id",
               {"n": channel_name, "un": channel_username, "t": clean_topics, "id": existing["id"]})
    else:
        db.run("INSERT INTO user_channels (user_id, channel_id, channel_name, channel_username, topics, created_at) "
               "VALUES (:u, :c, :n, :un, :t, :ts)",
               {"u": owner_id, "c": channel_id, "n": channel_name, "un": channel_username, "t": clean_topics, "ts": ts})
    return {"channel_id": channel_id, "channel_name": channel_name, "topics": clean_topics}


def set_channel_topics(owner_id: int, channel_row_id: int, topics: str) -> None:
    if owner_id <= 0 or not db.table_exists("user_channels"):
        raise JsonResult(False, "Avtorizatsiya kerak")
    clean_topics = _clean_topics(topics)
    if clean_topics:
        _release_topics_from_others(owner_id, clean_topics.split(","), channel_row_id)
    db.run("UPDATE user_channels SET topics = :t WHERE id = :id AND user_id = :u",
           {"t": clean_topics, "id": channel_row_id, "u": owner_id})


def delete_channel_for_owner(owner_id: int, channel_row_id: int) -> None:
    if owner_id <= 0 or not db.table_exists("user_channels"):
        return
    db.run("DELETE FROM user_channels WHERE id = :id AND user_id = :u", {"id": channel_row_id, "u": owner_id})


def delete_plan(plan_id: int, owner_id: int = 0) -> None:
    if not db.table_exists("plans"):
        return
    sql = "UPDATE plans SET status = 'deleted', updated_at = :u WHERE id = :id"
    params = {"u": _now_str(), "id": plan_id}
    if owner_id > 0:
        sql += " AND owner_id = :o"
        params["o"] = owner_id
    db.run(sql, params)


# --- Statistika ---

def _history_rows(owner_id: int = 0) -> list:
    if not db.table_exists("history"):
        return []
    if owner_id > 0:
        return db.all_("SELECT * FROM history WHERE user_id = :u ORDER BY year, month, day", {"u": owner_id})
    return db.all_("SELECT * FROM history ORDER BY year, month, day")


def _history_row_date(row: dict) -> str:
    return f"{int(row['year']):04d}-{int(row['month']):02d}-{int(row['day']):02d}"


def _pct(completed: int, total: int) -> float:
    return round((completed / total) * 100, 1) if total > 0 else 0.0


def _summarize(rows: list, start: str, end: str) -> dict:
    s = {"start": start, "end": end, "days": 0, "total_tasks": 0, "completed_tasks": 0, "percent": 0.0}
    for row in rows:
        date = _history_row_date(row)
        if date < start or date > end:
            continue
        s["days"] += 1
        s["total_tasks"] += int(row["total_tasks"])
        s["completed_tasks"] += int(row["completed_tasks"])
    s["percent"] = _pct(s["completed_tasks"], s["total_tasks"])
    return s


def _daily_series(rows: list, days: int = 14) -> list:
    m = {}
    for row in rows:
        date = _history_row_date(row)
        m.setdefault(date, {"total": 0, "completed": 0})
        m[date]["total"] += int(row["total_tasks"])
        m[date]["completed"] += int(row["completed_tasks"])
    result = []
    cursor = now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=max(0, days - 1))
    for _ in range(days):
        date = cursor.strftime("%Y-%m-%d")
        total = m.get(date, {}).get("total", 0)
        completed = m.get(date, {}).get("completed", 0)
        result.append({"date": date, "label": cursor.strftime("%d.%m"), "total_tasks": total,
                       "completed_tasks": completed, "percent": _pct(completed, total)})
        cursor += timedelta(days=1)
    return result


def _monthly_series(rows: list, months: int = 12) -> list:
    m = {}
    for row in rows:
        key = f"{int(row['year']):04d}-{int(row['month']):02d}"
        m.setdefault(key, {"total": 0, "completed": 0})
        m[key]["total"] += int(row["total_tasks"])
        m[key]["completed"] += int(row["completed_tasks"])
    result = []
    n = now()
    year, month = n.year, n.month
    # months-1 oy orqaga suramiz
    total_index = year * 12 + (month - 1) - (months - 1)
    for _ in range(months):
        y, mo = divmod(total_index, 12)
        mo += 1
        key = f"{y:04d}-{mo:02d}"
        total = m.get(key, {}).get("total", 0)
        completed = m.get(key, {}).get("completed", 0)
        label = datetime(y, mo, 1).strftime("%b %y")
        result.append({"period": key, "label": label, "total_tasks": total,
                       "completed_tasks": completed, "percent": _pct(completed, total)})
        total_index += 1
    return result


def _count_by_type(plans: list) -> dict:
    result = {"daily_todo": 0, "daily_plan": 0, "challenge": 0, "reminder": 0, "todo": 0, "super_todo": 0}
    for plan in plans:
        t = str(plan.get("plan_type") or "")
        result[t] = result.get(t, 0) + 1
    return result


def build_stats_payload(owner_id: int = 0) -> dict:
    rows = _history_rows(owner_id)
    plans = list_plans(owner_id)
    n = now()
    today = n.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.isoweekday() - 1)
    week_end = week_start + timedelta(days=6)
    last_day = calendar.monthrange(n.year, n.month)[1]
    month_start = today.replace(day=1)
    month_end = today.replace(day=last_day)
    year_start = today.replace(month=1, day=1)
    year_end = today.replace(month=12, day=31)

    return {
        "summary": _summarize(rows, "0000-01-01", "9999-12-31"),
        "periods": {
            "week": _summarize(rows, week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")),
            "month": _summarize(rows, month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")),
            "year": _summarize(rows, year_start.strftime("%Y-%m-%d"), year_end.strftime("%Y-%m-%d")),
        },
        # 14 emas — sayt endi Dinamika grafigini orqaga (eski kunlarga)
        # tortib skroll qilishga imkon beradi, shuning uchun bu yerda ham
        # yetarlicha uzoq tarix qaytarilishi kerak (aks holda 14 kundan
        # nariga o'tilganda Boostday chizig'i soxta ravishda 0 ko'rsatardi).
        "daily_series": _daily_series(rows, 400),
        "monthly_series": _monthly_series(rows, 12),
        "plan_breakdown": _count_by_type(plans),
    }


# =====================================================================
#  KUNLIK ODATLAR (habits)
#  Har kuni belgilangan vaqtda takrorlanadigan shaxsiy ishlar.
#  Rejimlar: everyday | odd | even | weekend | weekday
# =====================================================================
HABIT_MODES = {"everyday", "odd", "even", "weekend", "weekday"}
HABIT_MODE_LABEL = {
    "everyday": "Har kuni",
    "odd": "Toq kunlari",
    "even": "Juft kunlari",
    "weekend": "Dam olish kunlari",
    "weekday": "Ish kunlari",
}


def habit_mode_matches(mode: str, when) -> bool:
    """Shu kunda odat bajarilishi kerakmi.

    `odd`/`even` — Boostday rejalaridagi bilan AYNI qoida
    (scheduler.daily_mode_should_send): toq = Du/Chor/Juma,
    juft = Sesh/Pay/Shan, yakshanba ikkalasida ham yo'q.
    """
    mode = (mode or "everyday").lower()
    n = when.isoweekday()          # 1=Dushanba ... 7=Yakshanba
    if mode == "everyday":
        return True
    if mode == "weekend":
        return n in (6, 7)
    if mode == "weekday":
        return n <= 5
    if mode in ("odd", "even"):
        if n == 7:
            return False
        is_odd = (n % 2) == 1
        return is_odd if mode == "odd" else not is_odd
    return True


def _clean_remind(raw: str) -> str:
    """'60,30,15,5' ko'rinishidagi eslatma oraliqlarini tozalaydi."""
    out = []
    for part in str(raw or "").split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        v = int(part)
        if 0 <= v <= 720 and v not in out:
            out.append(v)
    out.sort(reverse=True)
    return ",".join(str(v) for v in out)


def _valid_time(raw: str) -> str:
    raw = str(raw or "").strip()
    if len(raw) == 5 and raw[2] == ":" and raw[:2].isdigit() and raw[3:].isdigit():
        h, m = int(raw[:2]), int(raw[3:])
        if 0 <= h < 24 and 0 <= m < 60:
            return f"{h:02d}:{m:02d}"
    return "22:00"


def list_habits(owner_id: int, for_date=None) -> list:
    """Odatlar ro'yxati. `for_date` berilsa har biriga `today`/`done` qo'shiladi."""
    if not db.table_exists("habits"):
        return []
    rows = db.all_(
        "SELECT id, name, at_time, week_mode, remind, note, sort_order, is_active "
        "FROM habits WHERE owner_id = :u AND is_deleted = 0 "
        "ORDER BY at_time ASC, sort_order ASC, id ASC",
        {"u": owner_id},
    )
    done_ids = set()
    if for_date is not None and rows:
        d = for_date.strftime("%Y-%m-%d")
        for r in db.all_("SELECT habit_id FROM habit_log WHERE done_date = :d", {"d": d}):
            done_ids.add(int(r["habit_id"]))

    out = []
    for r in rows:
        item = {
            "id": int(r["id"]), "name": r["name"], "time": r["at_time"],
            "week_mode": r["week_mode"], "remind": r["remind"],
            "note": r["note"] or "", "is_active": int(r["is_active"] or 0),
            "mode_label": HABIT_MODE_LABEL.get(r["week_mode"], r["week_mode"]),
        }
        if for_date is not None:
            item["today"] = bool(item["is_active"]) and habit_mode_matches(r["week_mode"], for_date)
            item["done"] = int(r["id"]) in done_ids
        out.append(item)
    return out


def save_habit(owner_id: int, payload: dict) -> int:
    name = str(payload.get("name") or "").strip()[:255]
    if not name:
        raise JsonResult(False, "Nomi kiritilmadi")
    data = {
        "u": owner_id, "n": name,
        "t": _valid_time(payload.get("time")),
        "w": (str(payload.get("week_mode") or "everyday").lower()
              if str(payload.get("week_mode") or "everyday").lower() in HABIT_MODES else "everyday"),
        "r": _clean_remind(payload.get("remind") or "60,30,15,5"),
        "note": (str(payload.get("note") or "").strip() or None),
        "a": 1 if str(payload.get("is_active", "1")) not in ("0", "", "false") else 0,
    }
    hid = int(payload.get("id") or 0)
    if hid > 0:
        data["id"] = hid
        db.run(
            "UPDATE habits SET name=:n, at_time=:t, week_mode=:w, remind=:r, note=:note, "
            "is_active=:a, updated_at=CURRENT_TIMESTAMP WHERE id=:id AND owner_id=:u", data,
        )
        return hid
    return db.run_returning_id(
        "INSERT INTO habits (owner_id, name, at_time, week_mode, remind, note, is_active) "
        "VALUES (:u,:n,:t,:w,:r,:note,:a)", data,
    )


def delete_habit(owner_id: int, habit_id: int) -> None:
    db.run("UPDATE habits SET is_deleted=1, updated_at=CURRENT_TIMESTAMP "
           "WHERE id=:id AND owner_id=:u", {"id": habit_id, "u": owner_id})


def toggle_habit_done(owner_id: int, habit_id: int, date_str: str) -> bool:
    """Bugungi belgini qo'yadi yoki oladi. Qaytaradi: yangi holat (bajarildimi)."""
    own = db.one("SELECT id, name FROM habits WHERE id=:id AND owner_id=:u AND is_deleted=0",
                 {"id": habit_id, "u": owner_id})
    if not own:
        raise JsonResult(False, "Odat topilmadi")
    have = db.one("SELECT id FROM habit_log WHERE habit_id=:h AND done_date=:d",
                  {"h": habit_id, "d": date_str})
    if have:
        db.run("DELETE FROM habit_log WHERE habit_id=:h AND done_date=:d",
               {"h": habit_id, "d": date_str})
        return False
    db.run("INSERT INTO habit_log (habit_id, done_date) VALUES (:h,:d) ON CONFLICT DO NOTHING",
           {"h": habit_id, "d": date_str})
    # Sayt statistikasida ham ko'rinsin
    try:
        db.log_activity("habit", own["name"], 1, "odat")
    except Exception:  # noqa: BLE001
        logger.exception("habit activity_log yozilmadi")
    return True


def habits_text_block(owner_id: int, for_date) -> str:
    """Kunlik xabarga qo'shiladigan "Kunlik odatlar" bo'limi (bo'sh bo'lsa '')."""
    items = [h for h in list_habits(owner_id, for_date) if h.get("today")]
    if not items:
        return ""
    lines = ["", "🔁 <b>Kunlik odatlar</b>"]
    for h in items:
        mark = "✅" if h.get("done") else "▫️"
        lines.append(f"{mark} {h['time']} — {h['name']}")
    return "\n".join(lines)


def handle_action(action: str, params: dict) -> dict:
    """action ni bajaradi va payload (dict) qaytaradi. JsonResult ko'tarilishi mumkin."""
    def s(key: str) -> str:
        return str(params.get(key, "") or "").strip()

    def i(key: str) -> int:
        try:
            return int(s(key) or 0)
        except ValueError:
            return 0

    owner_id = i("owner_id")

    # --- Telefon bildirishnomasi (Web Push) ---
    if action == "push_key":
        # Ochiq kalit — brauzer obuna bo'lish uchun ishlatadi (sir emas)
        return {"ok": True, "message": "OK",
                "key": settings.VAPID_PUBLIC_KEY,
                "enabled": bool(settings.VAPID_PUBLIC_KEY),
                "count": len(push_mod.subscriptions(owner_id))}

    if action == "push_subscribe":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        ep, p256, au = s("endpoint"), s("p256dh"), s("auth")
        if not ep or not p256 or not au:
            raise JsonResult(False, "Obuna ma'lumoti to'liq emas")
        db.run(
            "INSERT INTO push_subs (owner_id, endpoint, p256dh, auth, ua, is_active) "
            "VALUES (:u,:e,:p,:a,:ua,1) "
            "ON CONFLICT (endpoint) DO UPDATE SET owner_id=:u, p256dh=:p, auth=:a, "
            "ua=:ua, is_active=1",
            {"u": owner_id, "e": ep, "p": p256, "a": au, "ua": s("ua")[:255] or None})
        return {"ok": True, "message": "Bildirishnoma yoqildi",
                "count": len(push_mod.subscriptions(owner_id))}

    if action == "push_unsubscribe":
        db.run("UPDATE push_subs SET is_active = 0 WHERE endpoint = :e", {"e": s("endpoint")})
        return {"ok": True, "message": "O'chirildi",
                "count": len(push_mod.subscriptions(owner_id))}

    if action == "push_test":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        n = push_mod.send(owner_id, "✅ Bildirishnoma ishlayapti",
                          "Eslatmalar shu ko'rinishda keladi.", url="/#habits", tag="test")
        if not n:
            raise JsonResult(False, "Hech qanday qurilma ulanmagan — avval yoqing")
        return {"ok": True, "message": f"{n} ta qurilmaga yuborildi", "sent": n}

    # --- Kunlik odatlar ---
    if action == "habits_list":
        return {"ok": True, "message": "OK",
                "habits": list_habits(owner_id, now()),
                "modes": [{"k": k, "n": HABIT_MODE_LABEL[k]} for k in
                          ("everyday", "odd", "even", "weekday", "weekend")]}

    if action == "habits_save":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        save_habit(owner_id, params)
        return {"ok": True, "message": "Saqlandi", "habits": list_habits(owner_id, now())}

    if action == "habits_delete":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        delete_habit(owner_id, i("id"))
        return {"ok": True, "message": "O'chirildi", "habits": list_habits(owner_id, now())}

    if action == "habits_toggle":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        d = s("date") or now().strftime("%Y-%m-%d")
        state = toggle_habit_done(owner_id, i("id"), d)
        return {"ok": True, "message": "Belgilandi" if state else "Bekor qilindi",
                "done": state, "habits": list_habits(owner_id, now())}

    if action == "channels":
        return {"ok": True, "message": "OK", "channels": list_channels(owner_id)}

    if action == "add_channel":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        result = add_channel_for_owner(owner_id, s("channel"), s("topics"))
        return {"ok": True, "message": "Kanal ulandi", **result, "channels": list_channels(owner_id)}

    if action == "set_channel_topics":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        set_channel_topics(owner_id, i("id"), s("topics"))
        return {"ok": True, "message": "Mavzular belgilandi", "channels": list_channels(owner_id)}

    if action == "delete_channel":
        if owner_id <= 0:
            raise JsonResult(False, "Avtorizatsiya kerak")
        delete_channel_for_owner(owner_id, i("id"))
        return {"ok": True, "message": "Kanal o'chirildi", "channels": list_channels(owner_id)}

    if action == "list":
        rows = list_plans(owner_id)
        plans, reminders, todos, daily_routines = [], [], [], []
        for row in rows:
            pt = row["plan_type"]
            if pt == "reminder":
                reminders.append(row)
            elif pt in ("todo", "super_todo"):
                todos.append(row)
            elif pt == "daily_todo":
                daily_routines.append(row)
            else:
                plans.append(row)
        return {"ok": True, "message": "OK", "plans": plans, "reminders": reminders,
                "todos": todos, "daily_routines": daily_routines}

    if action == "get":
        pid = i("id")
        if pid <= 0:
            raise JsonResult(False, "ID topilmadi")
        item = get_plan(pid, owner_id)
        if not item:
            raise JsonResult(False, "Yozuv topilmadi")
        return {"ok": True, "message": "OK", "item": item}

    if action == "save":
        try:
            items = json.loads(params.get("items") or "[]")
        except (ValueError, TypeError):
            items = []
        payload = {
            "id": i("id"), "plan_type": s("plan_type"), "channel_id": s("channel_id"),
            "channel_name": s("channel_name"), "time": s("time"), "date": s("date"),
            "start_date": s("start_date"), "end_date": s("end_date"), "week_mode": s("week_mode"),
            "items": items if isinstance(items, list) else [],
            "tasks": decode_task_groups(params.get("tasks")),
            "owner_id": owner_id,
        }
        validate_payload(payload)
        # Xavfsizlik: kanal shu owner'ga tegishli bo'lishi shart (boshqaning kanaliga yozib bo'lmaydi).
        if owner_id > 0 and not channel_belongs_to(payload["channel_id"], owner_id):
            raise JsonResult(False, "Bu kanal sizga tegishli emas")
        saved_id = save_plan(payload)
        # Saytdan belgilangan vazifa Telegramdagi xabarda ham belgilanib qolsin.
        refresh_telegram_message(saved_id)
        return {"ok": True, "message": "Saqlandi", "id": saved_id}

    if action == "toggle_task":
        # Boostday "Bugungi ishlar" birlashtirilgan ro'yxatidan bitta vazifani
        # darhol belgilaydi (butun rejani tahrirlash oynasini ochmasdan).
        pid, index = i("id"), i("index")
        if pid <= 0 or index < 0:
            raise JsonResult(False, "Vazifa topilmadi")
        plan = db.one("SELECT * FROM plans WHERE id = :id AND status = 'active'", {"id": pid})
        if not plan:
            raise JsonResult(False, "Reja topilmadi")
        if owner_id > 0 and int(plan.get("owner_id") or 0) != owner_id:
            raise JsonResult(False, "Bu reja sizga tegishli emas")

        groups = decode_task_groups(plan["tasks"])
        tasks = flatten_task_groups(groups)
        if index >= len(tasks):
            raise JsonResult(False, "Vazifa topilmadi")

        current = int(tasks[index].get("status", 0) or 0)
        ts = now().strftime(DT_FMT)
        # super_todo — 3 holat (Telegram callback bilan bir xil mantiq: 0 kutmoqda ->
        # 2 boshlandi -> 1 tugadi); qolganlari — oddiy belgilash/bekor qilish.
        if plan["plan_type"] == "super_todo":
            if current == 0:
                tasks[index].update({"status": 2, "started_at": ts, "finished_at": None, "alerts": []})
                just_finished = False
            elif current == 2:
                tasks[index]["status"] = 1
                if not tasks[index].get("started_at"):
                    tasks[index]["started_at"] = ts
                tasks[index]["finished_at"] = ts
                just_finished = True
            else:
                tasks[index].update({"status": 0, "started_at": None, "finished_at": None, "alerts": []})
                just_finished = False
        else:
            new = 0 if current == 1 else 1
            tasks[index]["status"] = new
            just_finished = new == 1

        db.run("UPDATE plans SET tasks = :t, updated_at = :n WHERE id = :id",
               {"t": encode_task_groups(groups), "n": ts, "id": pid})

        if just_finished:
            from .helpers import log_task_finished, group_name_for_index
            log_task_finished(plan, str(tasks[index].get("text", "")), group_name_for_index(groups, index))
        elif int(tasks[index].get("status", 0)) == 0:
            # Qayta ochildi — bugungi jurnal yozuvi ham olib tashlanadi, aks
            # holda Sport bo'limi mashqni "bajarilgan" deb ko'rsataverardi.
            from .helpers import unlog_task_finished
            unlog_task_finished(str(tasks[index].get("text", "")))

        refresh_telegram_message(pid)
        return {"ok": True, "message": "Yangilandi", "status": int(tasks[index].get("status", 0))}

    if action == "delete":
        pid = i("id")
        if pid <= 0:
            raise JsonResult(False, "ID topilmadi")
        delete_plan(pid, owner_id)
        return {"ok": True, "message": "O'chirildi"}

    if action == "stats":
        return {"ok": True, "message": "OK", **build_stats_payload(owner_id)}

    raise JsonResult(False, "Noma'lum action")
