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

    A-05: Konstitutsiya §4 va Ustun 5 talabiga ko'ra audit jadvalidan hard DELETE
    qilish taqiqlanadi (Append-only Ledger). O'chirish o'rniga qarama-qarshi
    yozuv (compensating entry: unit='undo', meta='{"undo": true}') qo'shiladi.
    Tarix to'liq saqlanadi, o'qish so'rovlari (get_activity_log va sport._today_boost_done)
    esa juftlangan undo'larni SQL darajasida chiqarib tashlaydi.
    """
    section = s(body.get("section")).lower()
    if section not in ALLOWED_SECTIONS:
        raise ApiError("Noma'lum bo'lim.", 422)
    obj = s(body.get("object")).strip()
    if not obj:
        raise ApiError("Nomi berilmadi.", 422)

    ctx = owner_context(request)
    meta_val = json.dumps({"undo": True}, ensure_ascii=False)
    db.execute(
        "INSERT INTO activity_log (owner_type, owner_key, section, object_name, amount, unit, duration_seconds, meta) "
        "VALUES (:ot, :ok, :sec, :obj, NULL, :unit, NULL, :meta)",
        {
            "ot": ctx["owner_type"],
            "ok": ctx["owner_key"],
            "sec": section,
            "obj": obj[:255],
            "unit": "undo",
            "meta": meta_val,
        },
    )
    return success({"removed": 1})


def get_activity_log(request: Request, body: dict, date_from: str, date_to: str, section: str):
    """Faoliyat jurnalini o'qiydi.

    A-05: Append-only ledgerdagi juftlangan undo yozuvlari SQL darajasida (CTE orqali)
    chiqarib tashlanadi — Python siklida $O(N)$ sarflanmaydi.
    """
    ctx = owner_context(request)
    params: dict = {"ot": ctx["owner_type"], "ok": ctx["owner_key"]}

    date_from = (date_from or "").strip()
    date_to = (date_to or "").strip()
    section = (section or "").strip().lower()

    date_filter = ""
    if date_from:
        date_filter += " AND a.occurred_at >= :df"
        params["df"] = date_from
    if date_to:
        date_filter += " AND a.occurred_at < (CAST(:dt AS date) + INTERVAL '1 day')"
        params["dt"] = date_to

    sec_filter = ""
    if section:
        if section == "sport":
            sec_filter = " AND a.section IN ('sport', 'boostday')"
        else:
            sec_filter = " AND a.section = :sec"
            params["sec"] = section

    sql = f"""
        WITH undos AS (
            SELECT owner_type, owner_key,
                   CASE WHEN section IN ('sport', 'boostday') THEN 'sport' ELSE section END AS norm_sec,
                   lower(translate(trim(regexp_replace(object_name, '^[0-2]?[0-9]:[0-5][0-9]\\\\s*', '')), 'ʻ’`', '''''')) AS norm_obj,
                   CAST(occurred_at AS date) AS log_date,
                   COUNT(*) AS undo_count
            FROM activity_log
            WHERE owner_type = :ot AND owner_key = :ok AND unit = 'undo'
            GROUP BY owner_type, owner_key, norm_sec, norm_obj, log_date
        ),
        ranked_positives AS (
            SELECT a.*,
                   CASE WHEN a.section IN ('sport', 'boostday') THEN 'sport' ELSE a.section END AS norm_sec,
                   lower(translate(trim(regexp_replace(a.object_name, '^[0-2]?[0-9]:[0-5][0-9]\\\\s*', '')), 'ʻ’`', '''''')) AS norm_obj,
                   CAST(a.occurred_at AS date) AS log_date,
                   ROW_NUMBER() OVER (
                       PARTITION BY a.owner_type, a.owner_key,
                                    CASE WHEN a.section IN ('sport', 'boostday') THEN 'sport' ELSE a.section END,
                                    lower(translate(trim(regexp_replace(a.object_name, '^[0-2]?[0-9]:[0-5][0-9]\\\\s*', '')), 'ʻ’`', '''''')),
                                    CAST(a.occurred_at AS date)
                       ORDER BY a.occurred_at ASC, a.id ASC
                   ) AS rn
            FROM activity_log a
            WHERE a.owner_type = :ot AND a.owner_key = :ok AND a.unit != 'undo'
              {date_filter}
              {sec_filter}
        )
        SELECT rp.section, rp.object_name, rp.amount, rp.unit, rp.duration_seconds, rp.meta, rp.occurred_at
        FROM ranked_positives rp
        LEFT JOIN undos u
          ON u.owner_type = rp.owner_type
         AND u.owner_key = rp.owner_key
         AND u.norm_sec = rp.norm_sec
         AND u.norm_obj = rp.norm_obj
         AND u.log_date = rp.log_date
        WHERE rp.rn > COALESCE(u.undo_count, 0)
        ORDER BY rp.occurred_at DESC
        LIMIT 3000
    """
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
