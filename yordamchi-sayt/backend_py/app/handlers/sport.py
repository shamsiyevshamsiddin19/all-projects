"""Sport mashqlari: ro'yxat, yangilanish tekshiruvi, saqlash (media yuklash bilan), o'chirish."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import parse_qs, urlparse

from fastapi import Request
from sqlalchemy import text

from .. import db
from ..config import settings
from ..errors import ApiError, success
from ..owner import owner_context
from .common import s, to_float, to_int

# Mashqda nima o'sadi: og'irlik (shtanga), takror (turnik/brus), vaqt (planka),
# daqiqa va masofa (o'yin sportlari — basketbol/futbol mashqlari)
PROGRESS_TYPES = {"weight", "reps", "time", "min", "dist"}
# Qachon o'sadi: har kuni / juft kunlari / toq kunlari / kun ora / qo'lda
PROGRESS_MODES = {"daily", "even", "odd", "alternate", "manual"}

# ⚠️ Bu ro'yxat `assets/js/app2/sport.js` dagi `CATS` bilan BIR XIL bo'lishi
# shart. Bu yerda yo'q kategoriya `_empty_data()` ga tushmaydi va o'sha
# kategoriyadagi mashqlar saytga UMUMAN yetib bormaydi (jimgina yo'qoladi).
CATEGORIES = [
    "turnik", "brus", "ajimaniya", "full", "grud", "bitseps",
    "triseps", "orqa", "yelka", "oyoq", "press", "kardio", "armwresling",
    "futbol", "voleybol", "badminton", "basketbol",
]

IMAGE_EXT = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "avif"}
VIDEO_EXT = {"mp4", "webm", "ogg", "mov", "m4v", "avi", "mkv"}


def _empty_data() -> dict[str, list]:
    return {c: [] for c in CATEGORIES}


def _touch_sync(ctx: dict, conn=None) -> None:
    # meta_value — matn (VARCHAR); PostgreSQL timestamp'ni avtomatik matnga o'girmaydi,
    # shuning uchun to_char bilan aniq formatlaymiz. clock_timestamp() — mikrosoniya aniqligida
    # (bir soniyada bir nechta saqlash ham har xil qiymat beradi → yangilanish e'tibordan chetda qolmaydi).
    stamp = "to_char(clock_timestamp(), 'YYYY-MM-DD HH24:MI:SS.US')"
    sql = (
        "INSERT INTO sport_sync_meta (owner_type, owner_key, meta_key, meta_value) "
        f"VALUES (:ot, :ok, 'last_global_update', {stamp}) "
        "ON CONFLICT (owner_type, owner_key, meta_key) "
        f"DO UPDATE SET meta_value = {stamp}, updated_at = CURRENT_TIMESTAMP"
    )
    p = {"ot": ctx["owner_type"], "ok": ctx["owner_key"]}
    if conn is not None:
        conn.execute(text(sql), p)
    else:
        db.execute(sql, p)


def _sync_value(ctx: dict) -> str:
    row = db.fetch_one(
        "SELECT meta_value FROM sport_sync_meta "
        "WHERE owner_type = :ot AND owner_key = :ok AND meta_key = 'last_global_update' LIMIT 1",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if row and row.get("meta_value"):
        return str(row["meta_value"])
    _touch_sync(ctx)
    row = db.fetch_one(
        "SELECT meta_value FROM sport_sync_meta "
        "WHERE owner_type = :ot AND owner_key = :ok AND meta_key = 'last_global_update' LIMIT 1",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if row and row.get("meta_value"):
        return str(row["meta_value"])
    # DB'dan o'qib bo'lmasa ham server GMT'da bo'lgani uchun Toshkent vaqtiga aylantiramiz
    # (aks holda mijozning "oxirgi yangilanish" solishtiruvi soatlab noto'g'ri chiqib qolardi).
    return datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d %H:%M:%S")


def _build_data(ctx: dict) -> dict[str, list]:
    data = _empty_data()
    rows = db.fetch_all(
        "SELECT id, category, name, description, weight, increase_amount, set_count, rep_count, "
        "progress_type, progress_mode, start_date, start_time, end_time, updated_at "
        # `sort_order` — qo'lda belgilangan tartib (kichigi yuqorida).
        # Standart 0 bo'lgani uchun belgilanmagan mashqlar avvalgidek
        # `id` bo'yicha, ya'ni qo'shilish tartibida chiqadi.
        "FROM sport_exercises WHERE owner_type = :ot AND owner_key = :ok AND is_deleted = 0 "
        "ORDER BY sort_order ASC, id ASC",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if not rows:
        return data

    ids = [int(r["id"]) for r in rows]
    media_map: dict[int, list[str]] = {}
    if ids:
        # IN (:id0, :id1, ...) — nomli parametrlar bilan (injection'siz)
        placeholders = ", ".join(f":id{i}" for i in range(len(ids)))
        params = {f"id{i}": v for i, v in enumerate(ids)}
        media_rows = db.fetch_all(
            f"SELECT exercise_id, file_path FROM sport_media WHERE exercise_id IN ({placeholders}) "
            "ORDER BY sort_order ASC, id ASC",
            params,
        )
        for m in media_rows:
            media_map.setdefault(int(m["exercise_id"]), []).append(str(m["file_path"]))

    for r in rows:
        category = str(r["category"])
        if category not in data:
            continue
        rid = int(r["id"])
        data[category].append({
            "id": rid,
            "name": str(r["name"]),
            "desc": str(r["description"] or ""),
            "weight": float(r["weight"]),
            "increase": float(r["increase_amount"]),
            "sets": int(r["set_count"]),
            "reps": int(r["rep_count"]),
            "progress_type": str(r["progress_type"] or "weight"),
            "progress_mode": str(r["progress_mode"] or "daily"),
            "start_date": str(r["start_date"]) if r["start_date"] else "",
            "start_time": str(r["start_time"]) if r["start_time"] else "",
            "end_time": str(r["end_time"]) if r["end_time"] else "",
            "media": media_map.get(rid, []),
            "updated_at": str(r["updated_at"]),
        })
    return data


# Boostday vazifa matni "21:31 - 21:40 | Klassik otjimaniya" ko'rinishida
# bo'ladi. Mashq nomi bilan taqqoslashdan oldin vaqt prefiksi olib tashlanadi.
# (Bot tomonida ayni shu qoida: bot_py/app/helpers.py::normalize_task_name)
_TIME_PREFIX_SQL = r"^\s*[0-9]{1,2}:[0-9]{2}\s*[-–—]\s*[0-9]{1,2}:[0-9]{2}\s*\|\s*"

# O'zbekcha matnda apostrof bir necha xil belgi bilan yoziladi ("To'pni" /
# "Toʻpni") — taqqoslashdan oldin hammasi oddiy ' ga keltiriladi.
# (Ayni qoida: bot_py/app/helpers.py::_APOS, core.js::normTaskName)
_APOS_FROM = "ʻʼ‘’`´"
_APOS_TO = "''''''"


def _today_boost_done(ctx: dict) -> list[str]:
    """Bugun bajarilgan mashqlarning KANONIK nomlari (Telegram yoki saytdan).

    Ikki manba birlashtiriladi:
      1) `section='sport'` yozuvlari — bot endi sport vazifasini shu bo'limga
         yozadi (kanonik nom bilan);
      2) `section='boostday'` yozuvlari, agar nomi (vaqt prefiksi olib
         tashlangach) mashq nomiga mos kelsa — ESKI yozuvlar shu ko'rinishda
         qolgan va bot yangilanmagan holatda ham to'g'ri ishlashi uchun.

    Qaytariladigan nom DOIM `sport_exercises.name` dagi kanonik shakl —
    frontend uni to'g'ridan-to'g'ri mashq nomi bilan solishtiradi.
    """
    rows = db.fetch_all(
        """
        SELECT DISTINCT e.name AS name
          FROM activity_log a
          JOIN sport_exercises e
            ON lower(translate(trim(e.name), :af, :at))
             = lower(translate(trim(regexp_replace(a.object_name, :pfx, '')), :af, :at))
         WHERE a.owner_type = :ot AND a.owner_key = :ok
           AND a.section IN ('sport', 'boostday')
           AND a.occurred_at >= CURRENT_DATE
        """,
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "pfx": _TIME_PREFIX_SQL,
         "af": _APOS_FROM, "at": _APOS_TO},
    )
    return [str(r["name"]) for r in rows if r["name"]]


def get_all(request: Request, body: dict):
    ctx = owner_context(request)
    return success({
        "last_global_update": _sync_value(ctx),
        "data": _build_data(ctx),
        "today_boost_done": _today_boost_done(ctx),
    })


def check_updates(request: Request, body: dict, last_sync: str):
    ctx = owner_context(request)
    server_sync = _sync_value(ctx)
    return success({"has_updates": last_sync.strip() != server_sync, "last_global_update": server_sync})


# --- Media aniqlash / saqlash -----------------------------------------------

def _detect_media_type(mime: str, ext: str) -> str | None:
    mime = (mime or "").strip().lower()
    ext = (ext or "").strip().lower()
    if mime != "image/svg+xml" and (mime.startswith("image/") or ext in IMAGE_EXT):
        return "image"
    if mime.startswith("video/") or ext in VIDEO_EXT:
        return "video"
    return None


def _youtube_id(url: str) -> str:
    parts = urlparse(url)
    if not parts.hostname:
        return ""
    host = re.sub(r"^(www\.|m\.)", "", parts.hostname.lower())
    path = (parts.path or "").strip("/")
    if host == "youtu.be":
        return path.split("/")[0].strip()
    if host in ("youtube.com", "youtube-nocookie.com"):
        q = parse_qs(parts.query or "")
        if q.get("v"):
            return q["v"][0].strip()
        seg = path.split("/") if path else []
        if seg and seg[0] in ("shorts", "embed", "live") and len(seg) > 1:
            return seg[1].strip()
    return ""


def _detect_link_type(url: str) -> str | None:
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    if _youtube_id(url) != "":
        return "youtube"
    path = (parts.path or "").lower()
    if re.search(r"\.(mp4|webm|ogg|mov|m4v|avi|mkv)$", path):
        return "video_link"
    return None


async def _save_uploaded_files(files) -> dict:
    result = {"saved": [], "errors": []}
    upload_dir = Path(settings.UPLOAD_DIR) / "sport"
    upload_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        original = f.filename or "media"
        ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
        mime = f.content_type or ""
        media_type = _detect_media_type(mime, ext)
        if media_type is None:
            result["errors"].append(f"{original}: faqat rasm, GIF yoki video yuklang")
            continue
        safe_ext = re.sub(r"[^a-z0-9]", "", ext)
        new_name = f"sport_{uuid.uuid4().hex}" + (f".{safe_ext}" if safe_ext else "")
        target = upload_dir / new_name
        data = await f.read()
        target.write_bytes(data)
        result["saved"].append({"path": f"uploads/sport/{new_name}", "type": media_type})
    return result


def _save_media_links(links) -> dict:
    result = {"saved": [], "errors": []}
    if not isinstance(links, list):
        links = [links]
    seen = set()
    for link in links:
        url = s(link)
        if url == "" or url in seen:
            continue
        seen.add(url)
        t = _detect_link_type(url)
        if t is None:
            result["errors"].append(f"{url}: YouTube yoki bevosita video link kiriting")
            continue
        result["saved"].append({"path": url, "type": t})
    return result


async def save_exercise(request: Request):
    if request.method != "POST":
        raise ApiError("Faqat POST mumkin", 405)

    form = await request.form()
    ctx = owner_context(request)

    exercise_id = to_int(form.get("id"))
    category = s(form.get("category"))
    name = s(form.get("name"))
    desc = s(form.get("desc"))
    weight = to_float(form.get("weight"))
    increase = to_float(form.get("increase"))
    sets = to_int(form.get("sets"))
    reps = to_int(form.get("reps"))
    replace_media = bool(form.get("replace_media"))

    # Nima oshadi va qaysi kunlari oshadi
    progress_type = s(form.get("progress_type")).lower()
    if progress_type not in PROGRESS_TYPES:
        progress_type = "weight"
    progress_mode = s(form.get("progress_mode")).lower()
    if progress_mode not in PROGRESS_MODES:
        progress_mode = "daily"
    start_date = s(form.get("start_date")) or None
    start_time = s(form.get("start_time")) or ""
    end_time = s(form.get("end_time")) or ""

    if category not in CATEGORIES:
        raise ApiError("Noto'g'ri sport kategoriyasi", 422)
    if name == "":
        raise ApiError("Mashq nomini kiriting", 422)

    media_files = [v for v in form.getlist("media") if getattr(v, "filename", None)]
    media_links = form.getlist("media_links")

    upload_result = await _save_uploaded_files(media_files) if media_files else {"saved": [], "errors": []}
    link_result = _save_media_links(media_links) if media_links else {"saved": [], "errors": []}
    uploaded_media = upload_result["saved"] + link_result["saved"]
    upload_errors = upload_result["errors"] + link_result["errors"]
    media_submitted = bool(media_files) or bool(media_links)

    if media_submitted and not uploaded_media and upload_errors:
        raise ApiError("Media yuklanmadi: " + "; ".join(upload_errors), 422)

    with db.tx() as conn:
        if exercise_id > 0:
            conn.execute(
                text(
                    "UPDATE sport_exercises SET category = :c, name = :n, description = :d, weight = :w, "
                    "increase_amount = :inc, set_count = :sc, rep_count = :rc, is_deleted = 0, "
                    "progress_type = :pt, progress_mode = :pm, start_date = :sd, start_time = :st, end_time = :et "
                    "WHERE id = :id AND owner_type = :ot AND owner_key = :ok"
                ),
                {"c": category, "n": name, "d": desc, "w": weight, "inc": increase, "sc": sets, "rc": reps,
                 "pt": progress_type, "pm": progress_mode, "sd": start_date, "st": start_time, "et": end_time,
                 "id": exercise_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
            )
        else:
            res = conn.execute(
                text(
                    "INSERT INTO sport_exercises (owner_type, owner_key, category, name, description, weight, "
                    "increase_amount, set_count, rep_count, progress_type, progress_mode, start_date, start_time, end_time) "
                    "VALUES (:ot, :ok, :c, :n, :d, :w, :inc, :sc, :rc, :pt, :pm, :sd, :st, :et) RETURNING id"
                ),
                {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "c": category, "n": name, "d": desc,
                 "w": weight, "inc": increase, "sc": sets, "rc": reps,
                 "pt": progress_type, "pm": progress_mode, "sd": start_date, "st": start_time, "et": end_time},
            )
            exercise_id = int(res.scalar() or 0)

        if replace_media and uploaded_media:
            conn.execute(text("DELETE FROM sport_media WHERE exercise_id = :id"), {"id": exercise_id})

        for index, media in enumerate(uploaded_media):
            conn.execute(
                text("INSERT INTO sport_media (exercise_id, file_path, file_type, sort_order) VALUES (:e, :p, :t, :so)"),
                {"e": exercise_id, "p": media["path"], "t": media["type"], "so": index},
            )

        _touch_sync(ctx, conn=conn)

    return success({
        "message": "Mashq saqlandi",
        "last_global_update": _sync_value(ctx),
        "data": _build_data(ctx),
        "uploaded_media_count": len(uploaded_media),
        "upload_warnings": upload_errors,
    })


def delete_exercise(request: Request, body: dict):
    if request.method != "POST":
        raise ApiError("Faqat POST mumkin", 405)
    ctx = owner_context(request)
    exercise_id = to_int(body.get("id"))
    if exercise_id <= 0:
        raise ApiError("Mashq ID topilmadi", 422)
    db.execute(
        "UPDATE sport_exercises SET is_deleted = 1 WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"id": exercise_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    _touch_sync(ctx)
    return success({"message": "Mashq o'chirildi", "last_global_update": _sync_value(ctx)})
