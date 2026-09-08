"""Foydalanuvchilarni boshqarish (qo'shish, ruxsatlar berish, tahrirlash, o'chirish).

Faqat tizim egasi (admin) boshqara oladi.
"""

from __future__ import annotations

import json
import re
from fastapi import Request

from .. import db
from ..config import settings
from ..errors import ApiError, success

from ..security import hash_password, verify_password

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Tartib MUHIM: mobil pastki panel shu ketma-ketlikda quriladi
# (`bootstrap.js` -> buildBottom). Foydalanuvchi so'ragan tartib:
# Bosh, Testlar, Learn, Statistika, Profil.
# `profile` 2026-09-08 da qo'shildi — usiz foydalanuvchi o'z akkaunt
# parolini ko'ra olmasdi va chiqish tugmasiga yetib bormasdi.
DEFAULT_ALLOWED_SECTIONS = ["home", "fanlar", "languages", "stats", "profile"]


def _clean_user_code(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(raw or "")).upper()


def _require_admin(request: Request) -> None:
    role = request.session.get("role")
    email = (request.session.get("doktor_email") or "").strip().lower()
    if role == "admin" or (email and email in settings.ALLOWED_EMAILS):
        return
    raise ApiError("Faqat administrator uchun ruxsat berilgan.", 403)


def ensure_table() -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS foydalanuvchilar (
            id BIGSERIAL PRIMARY KEY,
            email VARCHAR(191) NOT NULL,
            ism VARCHAR(191) NOT NULL DEFAULT '',
            ruxsatlar JSONB NOT NULL DEFAULT '["home", "fanlar", "languages", "stats", "profile"]'::jsonb,
            holat VARCHAR(32) NOT NULL DEFAULT 'faol',
            kirish_kodi VARCHAR(255) DEFAULT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_foydalanuvchilar_email UNIQUE (email)
        )
    """)
    db.execute("ALTER TABLE foydalanuvchilar ADD COLUMN IF NOT EXISTS kirish_kodi VARCHAR(255) DEFAULT NULL")
    db.execute("CREATE INDEX IF NOT EXISTS idx_foydalanuvchilar_email ON foydalanuvchilar (LOWER(email))")


def list_users(request: Request, body: dict) -> object:
    _require_admin(request)
    ensure_table()
    rows = db.fetch_all(
        "SELECT id, email, ism, ruxsatlar, holat, "
        "(kirish_kodi IS NOT NULL AND kirish_kodi != '') AS kod_bor, "
        "created_at FROM foydalanuvchilar ORDER BY id ASC"
    )
    users = []
    for r in rows:
        ruxsatlar = r.get("ruxsatlar") or DEFAULT_ALLOWED_SECTIONS
        if isinstance(ruxsatlar, str):
            try:
                ruxsatlar = json.loads(ruxsatlar)
            except Exception:
                ruxsatlar = DEFAULT_ALLOWED_SECTIONS
        users.append({
            "id": r["id"],
            "email": r["email"],
            "ism": r.get("ism") or "",
            "ruxsatlar": ruxsatlar,
            "holat": r.get("holat") or "faol",
            "kod_bor": bool(r.get("kod_bor")),
            "created_at": str(r.get("created_at") or ""),
        })
    return success({"users": users})


def add_user(request: Request, body: dict) -> object:
    _require_admin(request)
    ensure_table()
    email = str(body.get("email") or "").strip().lower()
    ism = str(body.get("ism") or "").strip()
    raw_code = body.get("kirish_kodi")
    raw_ruxsatlar = body.get("ruxsatlar")

    if not email:
        raise ApiError("Google emailini kiriting.", 400)
    if not EMAIL_RE.match(email):
        raise ApiError("Email formati noto'g'ri.", 400)

    if email in settings.ALLOWED_EMAILS:
        raise ApiError("Bu email sayt egasi (admin) emaili hisoblanadi.", 400)

    existing = db.fetch_one(
        "SELECT id FROM foydalanuvchilar WHERE LOWER(email) = LOWER(:e) LIMIT 1",
        {"e": email},
    )
    if existing:
        raise ApiError("Bu email allaqachon foydalanuvchilar ro'yxatida bor.", 400)

    code_hash = None
    if raw_code is not None and str(raw_code).strip() != "":
        clean_code = _clean_user_code(raw_code)
        if len(clean_code) != 12:
            raise ApiError("Maxfiy kirish kodi roppa-rosa 12 ta belgidan iborat bo'lishi kerak.", 400)
        if len(set(clean_code)) < 4:
            raise ApiError("Kirish kodi juda oddiy. Kamida 4 xil belgi qatnashsin.", 400)
        code_hash = hash_password(clean_code)

    if isinstance(raw_ruxsatlar, list) and len(raw_ruxsatlar) > 0:
        ruxsatlar = [str(x).strip() for x in raw_ruxsatlar if str(x).strip()]
    else:
        ruxsatlar = list(DEFAULT_ALLOWED_SECTIONS)

    ruxsatlar_json = json.dumps(ruxsatlar, ensure_ascii=False)

    user_id = db.execute_returning_id(
        "INSERT INTO foydalanuvchilar (email, ism, ruxsatlar, holat, kirish_kodi) "
        "VALUES (:e, :ism, CAST(:r AS jsonb), 'faol', :kodi)",
        {"e": email, "ism": ism, "r": ruxsatlar_json, "kodi": code_hash},
    )

    return success({
        "message": "Foydalanuvchi muvaffaqiyatli qo'shildi.",
        "user": {
            "id": user_id,
            "email": email,
            "ism": ism,
            "ruxsatlar": ruxsatlar,
            "holat": "faol",
            "kod_bor": bool(code_hash),
        },
    })


def update_user(request: Request, body: dict) -> object:
    _require_admin(request)
    ensure_table()
    user_id = int(body.get("id") or 0)
    if not user_id:
        raise ApiError("Foydalanuvchi id topilmadi.", 400)

    existing = db.fetch_one("SELECT * FROM foydalanuvchilar WHERE id = :id LIMIT 1", {"id": user_id})
    if not existing:
        raise ApiError("Foydalanuvchi topilmadi.", 404)

    ism = str(body.get("ism") if body.get("ism") is not None else existing.get("ism") or "").strip()
    holat = str(body.get("holat") if body.get("holat") is not None else existing.get("holat") or "faol").strip()
    raw_code = body.get("kirish_kodi")
    raw_ruxsatlar = body.get("ruxsatlar")

    if raw_code is not None:
        raw_code_str = str(raw_code).strip()
        if raw_code_str == "":
            code_hash = None
            update_code = True
        else:
            clean_code = _clean_user_code(raw_code_str)
            if len(clean_code) != 12:
                raise ApiError("Maxfiy kirish kodi roppa-rosa 12 ta belgidan iborat bo'lishi kerak.", 400)
            if len(set(clean_code)) < 4:
                raise ApiError("Kirish kodi juda oddiy. Kamida 4 xil belgi qatnashsin.", 400)
            code_hash = hash_password(clean_code)
            update_code = True
    else:
        code_hash = existing.get("kirish_kodi")
        update_code = False

    if isinstance(raw_ruxsatlar, list):
        ruxsatlar = [str(x).strip() for x in raw_ruxsatlar if str(x).strip()]
    else:
        ruxsatlar = existing.get("ruxsatlar") or DEFAULT_ALLOWED_SECTIONS
        if isinstance(ruxsatlar, str):
            try:
                ruxsatlar = json.loads(ruxsatlar)
            except Exception:
                ruxsatlar = DEFAULT_ALLOWED_SECTIONS

    ruxsatlar_json = json.dumps(ruxsatlar, ensure_ascii=False)

    if update_code:
        db.execute(
            "UPDATE foydalanuvchilar SET ism = :ism, ruxsatlar = CAST(:r AS jsonb), "
            "holat = :h, kirish_kodi = :kodi, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
            {"id": user_id, "ism": ism, "r": ruxsatlar_json, "h": holat, "kodi": code_hash},
        )
    else:
        db.execute(
            "UPDATE foydalanuvchilar SET ism = :ism, ruxsatlar = CAST(:r AS jsonb), "
            "holat = :h, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
            {"id": user_id, "ism": ism, "r": ruxsatlar_json, "h": holat},
        )

    return success({
        "message": "Foydalanuvchi yangilandi.",
        "user": {
            "id": user_id,
            "email": existing["email"],
            "ism": ism,
            "ruxsatlar": ruxsatlar,
            "holat": holat,
            "kod_bor": bool(code_hash),
        },
    })


def delete_user(request: Request, body: dict) -> object:
    _require_admin(request)
    ensure_table()
    user_id = int(body.get("id") or 0)
    if not user_id:
        raise ApiError("Foydalanuvchi id topilmadi.", 400)

    db.execute("DELETE FROM foydalanuvchilar WHERE id = :id", {"id": user_id})
    return success({"message": "Foydalanuvchi o'chirildi."})
