"""LMS (lms.tuit.uz) sessiyasi — dars jadvalini tortib olish.

Mantiq `tatu-bots/lms` loyihasidan olindi, lekin ATAYLAB soddalashtirildi:
bu yerda faqat LOGIN + SEMESTRLAR + JADVAL kerak, shuning uchun `lxml` ishlatilmaydi
(jadval JSON, semestrlar esa oddiy regex bilan olinadi) — 945MB'lik serverga
ortiqcha og'ir bog'liqlik qo'shilmasin.

Xavfsizlik:
  * Parol FAQAT serverda, Fernet bilan shifrlangan holda saqlanadi
    (kalit: LMS_SECRET yoki SESSION_SECRET dan hosil qilinadi).
  * Parol hech qachon mijozga qaytarilmaydi — API faqat `has_password` beradi.
  * localStorage'ga yozilmaydi (u brauzerga va sinxronga tushadi).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastapi import Request

from .. import db
from ..config import settings
from ..errors import ApiError, success
from ..owner import owner_context
from .common import s, to_int

logger = logging.getLogger("yordamchi.lms")

TZ = ZoneInfo("Asia/Tashkent")
BASE = "https://lms.tuit.uz"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_TOKEN_RE = re.compile(r'name="_token"\s+value="([^"]+)"')
_SELECT_RE = re.compile(r'<select[^>]*name=["\']semester_id["\'][^>]*>(.*?)</select>', re.S | re.I)
_OPTION_RE = re.compile(r'<option[^>]*value=["\'](\d+)["\'][^>]*>(.*?)</option>', re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")

# LMS mashg'ulot turlari (tatu-bots/lms/parse.py bilan bir xil)
LESSON_TYPES = {1: "Ma'ruza", 2: "Amaliyot", 3: "Laboratoriya", 4: "Seminar",
                5: "Mustaqil ish", 6: "Kurs ishi", 7: "Malakaviy amaliyot"}
# Mashg'ulot odatda 1 juftlik = 90 daqiqa
LESSON_MINUTES = 90


def _clean(v: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", str(v or ""))).strip()


# ─────────────────────────── shifrlash ───────────────────────────

def _fernet():
    from cryptography.fernet import Fernet
    raw = (getattr(settings, "LMS_SECRET", "") or settings.SESSION_SECRET or "").encode()
    if not raw:
        raise ApiError("Server kaliti sozlanmagan (SESSION_SECRET).", 503)
    key = base64.urlsafe_b64encode(hashlib.sha256(b"lms:" + raw).digest())
    return Fernet(key)


def _encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def _decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


# ─────────────────────────── hisob yozuvi ───────────────────────────

def _account(ctx: dict) -> dict | None:
    return db.fetch_one(
        "SELECT * FROM lms_account WHERE owner_type = :ot AND owner_key = :ok LIMIT 1",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )


def _public(acc: dict | None) -> dict:
    """Mijozga BERILADIGAN ko'rinish — parol hech qachon qo'shilmaydi."""
    if not acc:
        return {"connected": False}
    return {
        "connected": True,
        "login": acc.get("login") or "",
        "student_name": acc.get("student_name") or "",
        "semester_id": int(acc.get("semester_id") or 0),
        "semester_name": acc.get("semester_name") or "",
        "auto_sync": bool(acc.get("auto_sync")),
        "last_sync": str(acc.get("last_sync") or ""),
        "last_error": acc.get("last_error") or "",
        "lessons": int(db.fetch_value(
            "SELECT COUNT(*) FROM lms_schedule WHERE owner_type = :ot AND owner_key = :ok",
            {"ot": acc["owner_type"], "ok": acc["owner_key"]},
        ) or 0),
    }


# ─────────────────────────── LMS klient ───────────────────────────

class LmsError(ApiError):
    pass


async def _login(client: httpx.AsyncClient, login: str, password: str) -> None:
    r = await client.get("/auth/login")
    m = _TOKEN_RE.search(r.text)
    if not m:
        raise ApiError("LMS login sahifasi o'zgargan (CSRF token topilmadi).", 502)
    r2 = await client.post("/auth/login", data={
        "_token": m.group(1),
        "login": login.strip(),
        "password": password,
        "g-recaptcha-response": "",
    })
    if "/auth/login" in str(r2.url) or "/login" in str(r2.url):
        raise ApiError("LMS login yoki parol xato.", 401)


def _parse_semesters(html: str) -> list[tuple[int, str]]:
    sel = _SELECT_RE.search(html)
    if not sel:
        return []
    return [(int(v), _clean(t)) for v, t in _OPTION_RE.findall(sel.group(1))]


def _pick_semester(sems: list[tuple[int, str]]) -> tuple[int, str]:
    """'Qayta o'qish' bo'lmagan eng katta id — odatda joriy faol semestr."""
    if not sems:
        return 0, ""
    normal = [x for x in sems if "qayta" not in x[1].lower()]
    return max(normal or sems, key=lambda x: x[0])


# Fan nomini oqim KODIdan ajratish. Haqiqiy LMS sarlavhalari:
#   "Ehtimollar va statistika-MTH009"
#   "Sun’iy intellekt asoslari (M)-FAI009-1"
#   "Hisoblash tafakkuri va dasturlashga kirish/-ICT003/"
#   "Murabbiylik soati-315-24 DIo‘"
# Ya'ni kod bir nechta "-" tutishi mumkin, shuning uchun rpartition XATO bo'ladi
# (u "FAI009-1" ni "FAI009" + "1" ga bo'lib, kodni fan nomiga yopishtirib
# yuborardi). To'g'ri qoida: CHAPDAN birinchi shunday "-" ki, undan keyingi
# qism kodga o'xshasin — qisqa, ichida RAQAM bo'lsin va faqat kod belgilaridan
# iborat bo'lsin. Raqam sharti "Ona tili - Adabiyot" kabi nomlarni bo'lib
# yubormaslik uchun.
_CODE_TAIL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\s\-/‘’'`]*$")


def _split_subject(body: str) -> tuple[str, str]:
    for i, ch in enumerate(body):
        if ch != "-" or i == 0:
            continue
        tail = body[i + 1:].strip()
        if not tail or len(tail) > 24:
            continue
        if not any(c.isdigit() for c in tail):
            continue
        if not _CODE_TAIL_RE.match(tail):
            continue
        head = body[:i].strip().rstrip("/").strip()
        if head:
            return head, tail.rstrip("/").strip()
    return body.strip().rstrip("/").strip(), ""


def _parse_schedule(data: dict) -> list[dict]:
    """Kalendar JSON'ini dars yozuvlariga aylantiradi.

    `title` odatda "(A-408)\\nFan nomi-KOD" ko'rinishida keladi.
    """
    out = []
    for ev in (data or {}).get("json", []):
        raw = str(ev.get("title") or "")
        room, body = "", raw
        first, _, rest = raw.partition("\n")
        if first.strip().startswith("(") and first.strip().endswith(")"):
            room, body = _clean(first).strip("()"), rest
        body = _clean(body)
        subject, stream = _split_subject(body)
        start = None
        if ev.get("start"):
            try:
                start = datetime.fromisoformat(str(ev["start"]))
            except ValueError:
                start = None
        if not start or not subject:
            continue
        code = to_int(ev.get("type"))
        end = start + timedelta(minutes=LESSON_MINUTES)
        out.append({
            "date": start.strftime("%Y-%m-%d"),
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "subject": subject,
            "stream": stream,
            "room": room,
            "type_name": LESSON_TYPES.get(code, "Mashg'ulot"),
        })
    out.sort(key=lambda x: (x["date"], x["start"]))
    return out


async def _fetch(login: str, password: str, semester_id: int = 0) -> dict:
    """Login qilib semestrlar ro'yxati va tanlangan semestr jadvalini oladi."""
    async with httpx.AsyncClient(
        base_url=BASE, timeout=40.0, follow_redirects=True,
        headers={"User-Agent": UA, "Accept-Language": "uz,ru;q=0.9,en;q=0.8"},
    ) as c:
        await _login(c, login, password)

        page = await c.get("/student/my-courses")
        sems = _parse_semesters(page.text)
        if semester_id and semester_id not in [x[0] for x in sems]:
            semester_id = 0
        sid, sname = (semester_id, dict(sems).get(semester_id, "")) if semester_id else _pick_semester(sems)
        if not sid:
            raise ApiError("LMS'da semestr topilmadi.", 502)

        r = await c.get(f"/student/schedule/load/{sid}",
                        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            raise ApiError("LMS jadval javobini o'qib bo'lmadi.", 502)

        # Talaba ismi (ixtiyoriy — topilmasa bo'sh qoladi)
        name = ""
        m = re.search(r'class="[^"]*user-name[^"]*"[^>]*>([^<]{3,80})<', page.text)
        if m:
            name = _clean(m.group(1))

        return {
            "semesters": [{"id": i, "name": n} for i, n in sems],
            "semester_id": sid, "semester_name": sname,
            "lessons": _parse_schedule(data),
            "student_name": name,
        }


# ─────────────────────────── saqlash ───────────────────────────

def _store(ctx: dict, lessons: list[dict]) -> int:
    """Jadvalni to'liq almashtiradi (LMS manba — haqiqat shu yerda)."""
    db.execute("DELETE FROM lms_schedule WHERE owner_type = :ot AND owner_key = :ok",
               {"ot": ctx["owner_type"], "ok": ctx["owner_key"]})
    for it in lessons:
        db.execute(
            "INSERT INTO lms_schedule (owner_type, owner_key, lesson_date, start_time, end_time, "
            "subject, stream, room, type_name) VALUES (:ot, :ok, :d, :st, :en, :su, :str, :ro, :tn)",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "d": it["date"],
             "st": it["start"], "en": it["end"], "su": it["subject"][:191],
             "str": it["stream"][:191], "ro": it["room"][:64], "tn": it["type_name"][:64]},
        )
    return len(lessons)


def _touch(ctx: dict, **fields) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    params = dict(fields)
    params.update({"ot": ctx["owner_type"], "ok": ctx["owner_key"]})
    db.execute(f"UPDATE lms_account SET {sets}, updated_at = CURRENT_TIMESTAMP "
               "WHERE owner_type = :ot AND owner_key = :ok", params)


# ─────────────────────────── API ───────────────────────────

def get_status(request: Request, body: dict):
    """Sozlamalar oynasi uchun holat (parolsiz)."""
    ctx = owner_context(request)
    acc = _account(ctx)
    out = _public(acc)
    if acc and acc.get("semesters"):
        try:
            out["semesters"] = json.loads(acc["semesters"])
        except (ValueError, TypeError):
            out["semesters"] = []
    return success(out)


async def connect(request: Request, body: dict):
    """Login/parolni tekshiradi, saqlaydi va jadvalni birinchi marta tortadi."""
    login = s(body.get("login")).strip()
    password = "" if body.get("password") is None else str(body.get("password"))
    if not login or not password:
        raise ApiError("Login va parol kerak.", 422)

    result = await _fetch(login, password, to_int(body.get("semester_id")))
    ctx = owner_context(request)
    enc = _encrypt(password)
    sems = json.dumps(result["semesters"], ensure_ascii=False)

    if _account(ctx):
        _touch(ctx, login=login, password_enc=enc, student_name=result["student_name"],
               semester_id=result["semester_id"], semester_name=result["semester_name"],
               semesters=sems, last_error="")
    else:
        db.execute(
            "INSERT INTO lms_account (owner_type, owner_key, login, password_enc, student_name, "
            "semester_id, semester_name, semesters, auto_sync) "
            "VALUES (:ot, :ok, :l, :p, :n, :si, :sn, :ss, TRUE)",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": login, "p": enc,
             "n": result["student_name"], "si": result["semester_id"],
             "sn": result["semester_name"], "ss": sems},
        )
    n = _store(ctx, result["lessons"])
    _touch(ctx, last_sync=datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"))
    out = _public(_account(ctx))
    out["semesters"] = result["semesters"]
    out["synced"] = n
    return success(out)


async def sync(request: Request, body: dict):
    """Saqlangan hisob bilan jadvalni qayta tortadi."""
    ctx = owner_context(request)
    acc = _account(ctx)
    if not acc:
        raise ApiError("Avval LMS hisobini ulang.", 400)
    try:
        password = _decrypt(acc["password_enc"])
    except Exception:  # noqa: BLE001
        raise ApiError("Saqlangan parolni ochib bo'lmadi — qayta ulang.", 400)

    sid = to_int(body.get("semester_id")) or int(acc.get("semester_id") or 0)
    try:
        result = await _fetch(acc["login"], password, sid)
    except ApiError as e:
        _touch(ctx, last_error=str(e.message)[:250])
        raise
    n = _store(ctx, result["lessons"])
    _touch(ctx, semester_id=result["semester_id"], semester_name=result["semester_name"],
           semesters=json.dumps(result["semesters"], ensure_ascii=False),
           student_name=result["student_name"] or (acc.get("student_name") or ""),
           last_sync=datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"), last_error="")
    out = _public(_account(ctx))
    out["semesters"] = result["semesters"]
    out["synced"] = n
    return success(out)


def get_schedule(request: Request, body: dict, date_from: str = "", date_to: str = ""):
    """Kun hisobi va bosh sahifa uchun — sana oralig'idagi darslar."""
    ctx = owner_context(request)
    where, params = "owner_type = :ot AND owner_key = :ok", {
        "ot": ctx["owner_type"], "ok": ctx["owner_key"]}
    if date_from:
        where += " AND lesson_date >= :df"
        params["df"] = date_from
    if date_to:
        where += " AND lesson_date <= :dt"
        params["dt"] = date_to
    rows = db.fetch_all(
        f"SELECT lesson_date, start_time, end_time, subject, stream, room, type_name "
        f"FROM lms_schedule WHERE {where} ORDER BY lesson_date, start_time", params)
    return success({"lessons": [{
        "date": str(r["lesson_date"])[:10], "start": str(r["start_time"])[:5],
        "end": str(r["end_time"])[:5], "subject": r["subject"], "stream": r["stream"] or "",
        "room": r["room"] or "", "type_name": r["type_name"] or "",
    } for r in rows]})


def set_options(request: Request, body: dict):
    """Avto-yangilash bayrog'i (semestr almashtirish `sync` orqali bo'ladi)."""
    ctx = owner_context(request)
    if not _account(ctx):
        raise ApiError("Avval LMS hisobini ulang.", 400)
    if "auto_sync" in body:
        _touch(ctx, auto_sync=bool(body.get("auto_sync")))
    return success(_public(_account(ctx)))


def disconnect(request: Request, body: dict):
    ctx = owner_context(request)
    db.execute("DELETE FROM lms_schedule WHERE owner_type = :ot AND owner_key = :ok",
               {"ot": ctx["owner_type"], "ok": ctx["owner_key"]})
    db.execute("DELETE FROM lms_account WHERE owner_type = :ot AND owner_key = :ok",
               {"ot": ctx["owner_type"], "ok": ctx["owner_key"]})
    return success({"connected": False})
