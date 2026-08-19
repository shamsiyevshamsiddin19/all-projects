"""Faoliyat jurnali: bo'limlarda qilingan har bir ish (Tarix/Grafik/Heatmap bo'limlari uchun poydevor)."""

from __future__ import annotations

import json
import logging

from fastapi import Request

from .. import db
from ..errors import ApiError, success
from ..owner import owner_context
from .common import s

logger = logging.getLogger("yordamchi.activity")

# Yozish nuqtalari: test yakunlanganda, mashq ✓ bosilganda, lug'at mashqi tugaganda,
# mavzu/material ochilganda, listening mashqida, Boostday vazifasi belgilanganda.
#
# ⚠️ BU RO'YXAT UCH JOY BILAN BIR XIL BO'LISHI SHART — bo'lim nomi tushunchasi
# to'rt joyda takrorlanadi va ular bir-biridan uzilib qolishi mumkin:
#     1) shu yerdagi ALLOWED_SECTIONS       (yozishga ruxsat)
#     2) assets/js/app2/tarix.js  — SEC + SEC_ORDER   (Tarix lentasi)
#     3) assets/js/app2/stats.js  — SEC_BLOCKS        (grafiklar)
#     4) Boostdaybot/bot_py/app/helpers.py — _section_for_group  (bot yozuvi)
# Ro'yxatda yo'q bo'lim JIMGINA tashlab yuborilardi — aynan shu sabab
# "Materiallar" bo'limi statistikaga umuman tushmay qolgan edi. Endi
# ogohlantirish yoziladi, shuning uchun kelgusida uzilish darrov ko'rinadi.
ALLOWED_SECTIONS = {"sport", "vocab", "quiz", "topic", "material",
                    "listening", "reading", "boostday"}


def _opt_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_int(value):
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def record(ctx: dict, section: str, object_name: str = "", amount=None, unit: str = "",
           duration=None, meta=None) -> None:
    """Server ichidan (boshqa handler'lardan) to'g'ridan-to'g'ri chaqiriladigan yozuv funksiyasi."""
    if section not in ALLOWED_SECTIONS:
        logger.warning("activity_log: noma'lum bo'lim '%s' — yozuv tashlab yuborildi "
                       "(ALLOWED_SECTIONS ga qo'shish kerakmi?)", section)
        return
    if isinstance(meta, (dict, list)):
        meta_val = json.dumps(meta, ensure_ascii=False)[:1000]
    elif meta is not None:
        meta_val = s(meta)[:1000]
    else:
        meta_val = None
    db.execute(
        "INSERT INTO activity_log (owner_type, owner_key, section, object_name, amount, unit, duration_seconds, meta) "
        "VALUES (:ot, :ok, :sec, :obj, :amt, :unit, :dur, :meta)",
        {
            "ot": ctx["owner_type"], "ok": ctx["owner_key"], "sec": section,
            "obj": s(object_name)[:255], "amt": amount, "unit": s(unit)[:32],
            "dur": duration, "meta": meta_val,
        },
    )


def log_activity(request: Request, body: dict):
    """Frontend'dan chaqiriladigan umumiy log action (lokal/klient hodisalar uchun)."""
    section = s(body.get("section")).lower()
    if section not in ALLOWED_SECTIONS:
        raise ApiError("Noma'lum bo'lim.", 422)
    ctx = owner_context(request)
    record(
        ctx, section,
        object_name=body.get("object"),
        amount=_opt_float(body.get("amount")),
        unit=body.get("unit") or "",
        duration=_opt_int(body.get("duration")),
        meta=body.get("meta"),
    )
    return success()


def unlog_activity(request: Request, body: dict):
    """Bugungi yozuvni BEKOR qiladi (belgilashni olib tashlash).

    Nega kerak: Sport bo'limi "bugun bajarilganmi" degan savolga qisman
    `activity_log` orqali javob beradi (Telegramdan belgilangani ham
    hisobga olinsin deb). Yozuvni o'chirish yo'li bo'lmagani uchun bir
    marta belgilangan mashqni QAYTA OLIB BO'LMASDI — mahalliy ro'yxatdan
    o'chirilsa ham server yozuvi uni "bajarilgan" deb ko'rsataverardi.

    Nom taqqoslash `sport.py` dagi qoida bilan bir xil: vaqt prefiksi
    olib tashlanadi, apostrof turlari birxillashtiriladi.
    """
    section = s(body.get("section")).lower()
    if section not in ALLOWED_SECTIONS:
        raise ApiError("Noma'lum bo'lim.", 422)
    obj = s(body.get("object")).strip()
    if not obj:
        raise ApiError("Nomi berilmadi.", 422)

    ctx = owner_context(request)
    # Sport uchun Boostday orqali yozilgan (vaqt prefiksli) yozuvlar ham o'chadi
    if section == "sport":
        from .sport import _TIME_PREFIX_SQL, _APOS_FROM, _APOS_TO
        n = db.execute(
            "DELETE FROM activity_log WHERE owner_type = :ot AND owner_key = :ok "
            "AND section IN ('sport', 'boostday') AND occurred_at >= CURRENT_DATE "
            "AND lower(translate(trim(regexp_replace(object_name, :pfx, '')), :af, :at)) "
            "  = lower(translate(trim(:obj), :af, :at))",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "obj": obj,
             "pfx": _TIME_PREFIX_SQL, "af": _APOS_FROM, "at": _APOS_TO},
        )
    else:
        n = db.execute(
            "DELETE FROM activity_log WHERE owner_type = :ot AND owner_key = :ok "
            "AND section = :sec AND object_name = :obj AND occurred_at >= CURRENT_DATE",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "sec": section, "obj": obj[:255]},
        )
    return success({"removed": n if isinstance(n, int) else None})


def get_activity_log(request: Request, body: dict, date_from: str, date_to: str, section: str):
    ctx = owner_context(request)
    sql = (
        "SELECT section, object_name, amount, unit, duration_seconds, meta, occurred_at "
        "FROM activity_log WHERE owner_type = :ot AND owner_key = :ok"
    )
    params: dict = {"ot": ctx["owner_type"], "ok": ctx["owner_key"]}

    date_from = (date_from or "").strip()
    date_to = (date_to or "").strip()
    section = (section or "").strip().lower()

    if date_from:
        sql += " AND occurred_at >= :df"
        params["df"] = date_from
    if date_to:
        # CAST(...) ishlatiladi, `:dt::date` EMAS — SQLAlchemy `::` dan oldingi
        # nomli parametrni bog'lamaydi va so'rov sintaksis xatosi bilan yiqiladi.
        sql += " AND occurred_at < (CAST(:dt AS date) + INTERVAL '1 day')"
        params["dt"] = date_to
    if section:
        sql += " AND section = :sec"
        params["sec"] = section

    sql += " ORDER BY occurred_at DESC LIMIT 3000"
    rows = db.fetch_all(sql, params)
    items = [
        {
            "section": r["section"],
            "object": r["object_name"] or "",
            "amount": float(r["amount"]) if r["amount"] is not None else None,
            "unit": r["unit"] or "",
            "duration": int(r["duration_seconds"]) if r["duration_seconds"] is not None else None,
            "meta": r["meta"],
            "at": r["occurred_at"].strftime("%Y-%m-%d %H:%M:%S") if r["occurred_at"] else "",
        }
        for r in rows
    ]
    return success({"items": items})
