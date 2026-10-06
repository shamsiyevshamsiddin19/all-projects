"""Yordamchi funksiyalar: sana/vaqt, matn, foydalanuvchi holati, kanal tahlili."""

from __future__ import annotations

import calendar
import html
import json
import logging
import re
from datetime import datetime, timedelta

from . import db
from .config import settings

logger = logging.getLogger("boostday")

DT_FMT = "%Y-%m-%d %H:%M:%S"


# --- Sana/vaqt (konfiguratsiyadagi timezone bilan) ---

def now() -> datetime:
    return datetime.now(settings.tz)


def now_str() -> str:
    return now().strftime(DT_FMT)


def today_str() -> str:
    return now().strftime("%Y-%m-%d")


# --- Sport <-> Boostday bog'lanishi ---
# Vazifa matni Sport bo'limidagi mashq nomiga mos kelsa, uning bajarilishi
# activity_log'ga section='sport' bilan yoziladi — Sport bo'limi, Statistika va
# Tarix hammasi bitta manbadan oziqlanadi.
#
# MUHIM (oldingi versiyadagi ikkita xato):
#   1) `log_task_finished` HAR DOIM section='boostday' yozardi, sayt esa
#      section='sport' bo'yicha qidirardi — Telegramda belgilangan mashq Sport
#      bo'limiga HECH QACHON yetib bormasdi.
#   2) "vazifa matni mashq nomi bilan AYNAN bir xil" deb hisoblangan edi, lekin
#      haqiqiy ma'lumotda matn "21:31 - 21:40 | Klassik otjimaniya" ko'rinishida —
#      vaqt prefiksi bor. Shuning uchun taqqoslashdan oldin NORMALLASHTIRILADI.
#
# Kanal mavzusi (`channel_topics`) bu yerda ishlatilmaydi: bitta kanalda ham
# sport, ham boshqa (masalan rus tili) vazifalari bo'ladi, ya'ni kanal darajasi
# vazifani ajratish uchun yetarli emas. Nom bo'yicha moslik aniq va per-vazifa.

_TIME_PREFIX_RE = re.compile(r"^\s*\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2}\s*\|\s*")

# O'zbekcha matnda apostrof bir necha xil belgi bilan yoziladi (klaviatura,
# nusxa-ko'chirish, avtomatik almashtirish). "To'pni" va "Toʻpni" — turli
# belgilar, ular birxillashtirilmasa mashq nomi bilan mos kelmay qoladi.
_APOS = str.maketrans({"ʻ": "'", "ʼ": "'", "‘": "'",
                       "’": "'", "`": "'", "´": "'"})


def normalize_task_name(text) -> str:
    """Vazifa matnini taqqoslash uchun toza nomga keltiradi.

    "21:31 - 21:40 | Klassik otjimaniya" -> "Klassik otjimaniya"
    Apostrof turlari birxillashtiriladi, ketma-ket bo'shliqlar bittaga keladi.
    """
    s = _TIME_PREFIX_RE.sub("", str(text or "")).translate(_APOS)
    return " ".join(s.split()).strip()


def sport_exercise_name(task_text) -> str:
    """Vazifa sport mashqiga mos kelsa uning KANONIK nomini, aks holda '' qaytaradi.

    Kanonik nom muhim: activity_log'ga mashqning bazadagi nomi yoziladi, shunda
    sayt tomoni uni to'g'ridan-to'g'ri taniydi (vaqt prefiksisiz, bir xil registr).
    """
    clean = normalize_task_name(task_text)
    if not clean:
        return ""
    try:
        row = db.one(
            "SELECT name FROM sport_exercises WHERE lower(trim(name)) = lower(:n) LIMIT 1",
            {"n": clean},
        )
    except Exception:  # noqa: BLE001 — sport jadvali bo'lmasa ham bot ishlayversin
        logger.exception("sport_exercises so'rovi bajarilmadi")
        return ""
    return str(row["name"]) if row else ""
def channel_topics(channel_id: str) -> list[str]:
    if not channel_id:
        return []
    row = db.one("SELECT topics FROM user_channels WHERE channel_id = :c AND topics != '' LIMIT 1", {"c": channel_id})
    if not row or not row.get("topics"):
        return []
    return [t.strip() for t in str(row["topics"]).split(",") if t.strip()]


def group_name_for_index(groups: list, index: int) -> str:
    """flatten_task_groups() bilan bir xil tartibda — index qaysi bo'limga tegishli ekanini topadi."""
    i = 0
    for g in groups:
        n = len(g.get("tasks") or [])
        if index < i + n:
            return g.get("name") or ""
        i += n
    return ""


def unlog_task_finished(task_text: str) -> None:
    """Vazifa QAYTA OCHILGANDA bugungi jurnal yozuvini olib tashlaydi.

    Nega kerak: sport vazifasi `activity_log`ga yoziladi va Sport bo'limi
    "bugun bajarilganmi" degan savolga shu jadval orqali javob beradi.
    Yozuv o'chirilmasa, Telegramda belgini olib tashlagan bilan ham mashq
    saytda "bajarilgan" bo'lib turaverardi.
    """
    try:
        sport = sport_exercise_name(task_text)
        if not sport:
            return          # sport bo'lmagan vazifa uchun tarix saqlanadi
        db.run(
            "DELETE FROM activity_log WHERE owner_type = 'global' AND owner_key = 'shared' "
            "AND section = 'sport' AND object_name = :obj AND occurred_at >= CURRENT_DATE",
            {"obj": sport[:255]},
        )
    except Exception:  # noqa: BLE001
        logger.exception("activity_log yozuvini o'chirib bo'lmadi")


def log_task_finished(plan: dict, task_text: str, group_name: str = "") -> None:
    """Bajarilgan vazifani umumiy jurnalga yozadi.

    Vazifa sport mashqi bo'lsa section='sport' (o'z sohasiga) yoziladi —
    shunda Sport bo'limi, Statistika va Tarix uni bir xil ko'radi. Aks holda
    section='boostday'. `meta.via` manbani saqlaydi.
    """
    try:
        sport = sport_exercise_name(task_text)
        section = "sport" if sport else "boostday"
        obj = (sport or str(task_text or ""))[:255]

        # Sport uchun kuniga BITTA yozuv: bir mashq Telegramdan ham, saytdan ham
        # belgilanishi mumkin — statistikada ikki marta sanalmasligi kerak.
        if section == "sport":
            dup = db.one(
                "SELECT 1 FROM activity_log WHERE owner_type = 'global' AND owner_key = 'shared' "
                "AND section = 'sport' AND object_name = :obj AND occurred_at >= CURRENT_DATE LIMIT 1",
                {"obj": obj},
            )
            if dup:
                return

        db.log_activity(section, object_name=obj, amount=1, unit="vazifa",
                         meta=json.dumps({
                             "plan_type": plan.get("plan_type"),
                             "via": "boostday",
                             "group": group_name or "Umumiy",
                             "task": normalize_task_name(task_text) if sport else "",
                         }, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        logger.exception("activity_log yozib bo'lmadi (plan_id=%s)", plan.get("id"))


def date_str(value) -> str:
    """DB DATE/DATETIME obyektini yoki stringni 'YYYY-MM-DD' ko'rinishiga keltiradi.

    psycopg DATE/TIMESTAMP ustunlarini date/datetime obyekt qilib qaytaradi; kod esa
    ko'p joyda string kutadi. Bu yordamchi ikkalasini ham qo'llaydi.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return value.strftime("%Y-%m-%d")  # date yoki datetime
    except Exception:
        return str(value)


def valid_date(value) -> bool:
    try:
        datetime.strptime(date_str(value), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def valid_time(t: str) -> bool:
    return re.match(r"^(2[0-3]|[01]?[0-9]):([0-5][0-9])$", t or "") is not None


def month_name_uz(month: int) -> str:
    names = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
        7: "Iyul", 8: "Avgust", 9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr",
    }
    return names.get(month, str(month))


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def age_text(birth_date) -> str:
    birth_date = date_str(birth_date)
    if not birth_date or not valid_date(birth_date):
        return "Noma’lum"
    b = datetime.strptime(birth_date, "%Y-%m-%d")
    n = datetime.strptime(today_str(), "%Y-%m-%d")
    years = n.year - b.year
    months = n.month - b.month
    days = n.day - b.day
    if days < 0:
        months -= 1
        prev_month = n.month - 1 or 12
        prev_year = n.year if n.month > 1 else n.year - 1
        days += days_in_month(prev_year, prev_month)
    if months < 0:
        years -= 1
        months += 12
    return f"{years} yosh, {months} oy, {days} kun"


def progress_bar(percent: float, size: int = 10) -> str:
    filled = int((percent / 100) * size)
    filled = max(0, min(size, filled))
    return "■" * filled + "□" * (size - filled)


def next_datetime_for_daily(time_str: str, reference: datetime | None = None) -> str:
    ref = reference or now()
    run = datetime.strptime(f"{ref.strftime('%Y-%m-%d')} {time_str}:00", DT_FMT).replace(tzinfo=settings.tz)
    if run <= ref:
        run += timedelta(days=1)
    return run.strftime(DT_FMT)


# --- Matn ---

def escape_html(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def bot_signature() -> str:
    """Post oxiridagi bot imzosi (masalan "@boostdaybot").

    Bot useri `.env` dagi BOT_USERNAME dan olinadi — kodda QATTIQ YOZILMAYDI,
    shuning uchun loyihani boshqa bot uchun ishlatganda hech narsani
    tahrirlash shart emas. BOT_USERNAME bo'sh bo'lsa imzo umuman qo'shilmaydi.
    """
    username = (settings.BOT_USERNAME or "").strip().lstrip("@")
    return f"@{username}" if username else ""


def starts_with(haystack: str, needle: str) -> bool:
    return (haystack or "").startswith(needle)


# --- Vazifalarni bo'limlarga (guruhlarga) ajratish ---
#
# DB `tasks` ustunida ikki format qo'llab-quvvatlanadi:
#   1) Tekis (eski/oddiy):  [{"text":..,"status":0}, ...]
#   2) Bo'limli (yangi):    {"groups": [{"name": "Ish", "tasks": [...]}, ...]}
# Har ikkalasi ham decode_task_groups() orqali bir xil ko'rinishga ([{"name","tasks"}])
# keltiriladi. Vazifa raqamlari (va callback_data indekslari) BUTUN reja bo'yicha
# uzluksiz — bo'lim faqat vizual sarlavha, indekslash mantiqiga ta'sir qilmaydi.

def decode_task_groups(raw) -> list:
    if not raw:
        return [{"name": "", "time": "", "cat": "", "tasks": []}]
    try:
        v = json.loads(raw)
    except (ValueError, TypeError):
        return [{"name": "", "time": "", "cat": "", "tasks": []}]
    if isinstance(v, list):
        return [{"name": "", "time": "", "cat": "", "tasks": v}]
    if isinstance(v, dict) and isinstance(v.get("groups"), list):
        out = []
        for g in v["groups"]:
            if isinstance(g, dict):
                out.append({
                    "name": str(g.get("name") or ""),
                    # Vaqt oralig'i BUTUN BO'LIMGA tegishli ("08:00 - 08:30").
                    # Ilgari u har bir vazifa MATNI ichida prefiks bo'lib
                    # turardi; endi bo'lim darajasida, chunki amalda bir
                    # bo'limdagi ishlar bitta oraliqda bajariladi.
                    "time": str(g.get("time") or ""),
                    # `cat` — TURKUM (sport/rus/dasturlash/kurs/hayot/boshqa).
                    # Sayt Kun hisobida bo'lim RANGI shundan olinadi, shuning
                    # uchun bot uni o'zgartirmasdan olib yuradi.
                    "cat": str(g.get("cat") or ""),
                    "tasks": g["tasks"] if isinstance(g.get("tasks"), list) else [],
                })
        return out or [{"name": "", "time": "", "cat": "", "tasks": []}]
    return [{"name": "", "time": "", "cat": "", "tasks": []}]


def flatten_task_groups(groups: list) -> list:
    flat = []
    for g in groups:
        flat.extend(g.get("tasks") or [])
    return flat


def encode_task_groups(groups: list) -> str:
    # Bo'lim VAQTI ham guruhli shaklni talab qiladi: yassi ro'yxatda
    # saqlansa vaqt yo'qolib ketardi (nomsiz bitta bo'limga vaqt
    # qo'yilgan holat aynan shunday edi).
    def has_meta(g):
        return (str(g.get("name") or "").strip() != ""
                or str(g.get("time") or "").strip() != ""
                or str(g.get("cat") or "").strip() != "")

    is_grouped = len(groups) > 1 or (len(groups) == 1 and has_meta(groups[0]))
    if is_grouped:
        clean = [{
            "name": str(g.get("name") or ""),
            "time": str(g.get("time") or ""),
            "cat": str(g.get("cat") or ""),
            "tasks": g.get("tasks") or [],
        } for g in groups]
        return json.dumps({"groups": clean}, ensure_ascii=False)
    return json.dumps(flatten_task_groups(groups), ensure_ascii=False)


def build_todo_text(groups: list, title: str = "🗓 TO-DO") -> str:
    flat = flatten_task_groups(groups)
    total = len(flat)
    completed = sum(1 for t in flat if int(t.get("status", 0) or 0) == 1)
    percent = round((completed / total) * 100, 1) if total > 0 else 0

    lines = [f"<b>{title}</b>", f"📊 Progress: <b>{completed}/{total}</b> | <b>{percent}%</b>", ""]

    # Bo'lim sarlavhasi vaqt tufayli ham kerak bo'lishi mumkin (nomsiz,
    # lekin vaqti bor bo'lim — vaqt ko'rinmay qolmasin).
    show_headers = len(groups) > 1 or (
        len(groups) == 1 and (
            (groups[0].get("name") or "").strip() != ""
            or (groups[0].get("time") or "").strip() != ""
        )
    )
    counter = 0
    for gi, g in enumerate(groups):
        g_tasks = g.get("tasks") or []
        if not g_tasks:
            continue
        if show_headers:
            g_completed = sum(1 for t in g_tasks if int(t.get("status", 0) or 0) == 1)
            g_name = (g.get("name") or "").strip()
            g_time = (g.get("time") or "").strip()
            header = f"{gi + 1}-bo'lim" + (f": {escape_html(g_name)}" if g_name else "")
            time_part = f" 🕒 {escape_html(g_time)}" if g_time else ""
            lines.append(f"<b>{header}</b>{time_part} ({g_completed}/{len(g_tasks)})")
        for task in g_tasks:
            counter += 1
            status = int(task.get("status", 0) or 0)
            mark = "✅" if status == 1 else ("⏱" if status == 2 else "▫️")
            duration = f" ({task['duration']} daq)" if task.get("duration") else ""
            timer = ""
            if status == 2 and task.get("started_at") and task.get("duration"):
                try:
                    started = datetime.strptime(task["started_at"], DT_FMT).replace(tzinfo=settings.tz)
                    end_ts = started + timedelta(minutes=int(task["duration"]))
                    left_sec = (end_ts - now()).total_seconds()
                    if left_sec > 0:
                        timer = f" | qoldi: {max(1, int((left_sec + 59) // 60))} daq"
                    else:
                        timer = " | vaqt tugadi"
                except (ValueError, TypeError):
                    timer = ""
            lines.append(f"{counter}. {mark} {escape_html(task.get('text', ''))}{duration}{timer}")
        if show_headers:
            lines.append("")

    if not show_headers:
        lines.append("")
    signature = bot_signature()
    if signature:
        lines.append(signature)
    return "\n".join(lines)


def todo_keyboard(plan_id: int, groups: list, plan_type: str = "") -> dict:
    rows = []
    current = []
    counter = 0
    for g in groups:
        g_tasks = g.get("tasks") or []
        if not g_tasks:
            continue
        if current:
            rows.append(current)
            current = []
        for task in g_tasks:
            i = counter
            number = i + 1
            status = int(task.get("status", 0) or 0)
            is_done = status == 1
            text = ("✅" + str(number)) if is_done else str(number)
            if plan_type == "super_todo":
                if status == 2:
                    text = f"Tugatish {number}"
                elif is_done:
                    text = f"Qayta {number}"
                else:
                    text = f"Boshlash {number}"
            current.append({"text": text, "callback_data": f"todo_toggle:{plan_id}:{i}"})
            counter += 1
            if len(current) == 4:
                rows.append(current)
                current = []
    if current:
        rows.append(current)
    return {"inline_keyboard": rows}


# --- Foydalanuvchi holati ---

def normalize_user(from_: dict) -> dict:
    return {
        "chat_id": int(from_["id"]),
        "first_name": from_.get("first_name", "") or "",
        "username": from_.get("username", "") or "",
    }


def user_get_or_create(from_: dict) -> dict:
    u = normalize_user(from_)
    ts = now_str()
    user = db.one("SELECT * FROM users WHERE chat_id = :c", {"c": u["chat_id"]})
    if not user:
        db.run(
            "INSERT INTO users (chat_id, first_name, username, created_at, updated_at) "
            "VALUES (:c, :f, :u, :n, :n)",
            {"c": u["chat_id"], "f": u["first_name"], "u": u["username"], "n": ts},
        )
    else:
        db.run(
            "UPDATE users SET first_name = :f, username = :u, updated_at = :n WHERE id = :id",
            {"f": u["first_name"], "u": u["username"], "n": ts, "id": user["id"]},
        )
    return db.one("SELECT * FROM users WHERE chat_id = :c", {"c": u["chat_id"]})


def user_update_step(user_id: int, step: str | None, temp_data: dict | None = None) -> None:
    db.run(
        "UPDATE users SET step = :s, temp_data = :t, updated_at = :n WHERE id = :id",
        {
            "s": step,
            "t": json.dumps(temp_data, ensure_ascii=False) if temp_data is not None else None,
            "n": now_str(),
            "id": user_id,
        },
    )


def user_temp(user: dict) -> dict:
    if not user.get("temp_data"):
        return {}
    try:
        d = json.loads(user["temp_data"])
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


def reset_user_flow(user_id: int) -> None:
    user_update_step(user_id, None, None)


# --- Kanal tahlili ---

def normalize_channel_candidates(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if raw == "":
        return []
    m = re.match(r"^@([A-Za-z0-9_]{5,})$", raw)
    if m:
        return ["@" + m.group(1)]
    m = re.match(r"^https?://t\.me/([A-Za-z0-9_]{5,})/?$", raw, re.IGNORECASE)
    if m:
        return ["@" + m.group(1)]
    if re.match(r"^-100\d+$", raw):
        return [raw]
    if re.match(r"^-\d+$", raw):
        return [raw]
    if re.match(r"^\d+$", raw):
        return ["-100" + raw, raw]
    return []


def parse_channel_input(message: dict) -> dict | None:
    text = (message.get("text") or "").strip()
    if message.get("forward_from_chat"):
        chat = message["forward_from_chat"]
        return {
            "channel_id": str(chat["id"]),
            "channel_name": chat.get("title", "Forward qilingan chat"),
            "channel_username": ("@" + chat["username"]) if chat.get("username") else None,
        }
    if text != "":
        candidates = normalize_channel_candidates(text)
        if candidates:
            return {
                "channel_id": candidates[0],
                "channel_candidates": candidates,
                "channel_name": candidates[0],
                "channel_username": candidates[0] if candidates[0].startswith("@") else None,
            }
    return None
