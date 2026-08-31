"""Favqulodda kirish kodi — Google ishlamay qolganda ikkinchi yo'l.

NIMA UCHUN KERAK
================
Sayt faqat Google orqali ochiladi. Bu odatda yaxshi, lekin egasini o'z
saytidan tashqarida qoldirib qo'yishi mumkin:
  - boshqa qurilmada Google akkaunti ochilmagan bo'lsa;
  - saytga boshqa domendan kirilsa (OAuth "Authorized origins" ro'yxatida
    bo'lmagan domenda Google tugmasi ishlamaydi);
  - Google xizmati vaqtincha ishlamasa.

Shu sabab 14 belgilik kod bilan ham kirish mumkin.

XAVFSIZLIK QARORLARI
====================
1. FAIL-CLOSED. Kod YO'Q bo'lsa bu yo'l butunlay yopiq. Ya'ni xususiyat
   o'zi-o'zidan teshik ochmaydi — egasi uni ataylab yoqishi kerak.

2. Kod OCHIQ SAQLANMAYDI. Bazada faqat bcrypt xeshi turadi. Yaratilganda
   bir marta ko'rsatiladi va boshqa hech qachon ko'rsatilmaydi — yo'qotilsa
   yangisi yasaladi.

3. Xesh `app_storage` da EMAS, alohida jadvalda. Sabab: `storage_bootstrap`
   butun `app_storage` ni mijozga yuboradi — xesh o'sha yerda tursa,
   brauzerga ochiq uzatilardi.

4. Kod uzunligi 14 belgi, alifboda 31 ta belgi (chalkashadiganlari —
   0/O, 1/I/L — olib tashlangan). Bu ~31^14 ≈ 2.5 x 10^20 variant, ya'ni
   taxmin qilib topib bo'lmaydi. Ustiga kirish urinishlari IP bo'yicha
   cheklangan (`check_login_rate_limit`).

5. Kod XOTIRADA solishtiriladi (`bcrypt.checkpw`) — u doimiy vaqtda
   ishlaydi, ya'ni javob tezligiga qarab belgi taxmin qilib bo'lmaydi.
"""
from __future__ import annotations

import secrets
from datetime import datetime

from . import db
from .security import hash_password, verify_password

# Chalkashadigan belgilar yo'q: 0/O, 1/I/L olib tashlangan.
# Kod qo'lda ko'chiriladi, shuning uchun o'qilishi muhim.
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
CODE_LEN = 14


def ensure_table() -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS auth_codes ("
        " id SERIAL PRIMARY KEY,"
        " code_hash TEXT NOT NULL,"
        " created_at TIMESTAMP NOT NULL DEFAULT NOW(),"
        " last_used_at TIMESTAMP"
        ")"
    )


def normalize(raw: str) -> str:
    """Foydalanuvchi kodni chiziqcha/bo'shliq bilan yozishi mumkin.

    Ko'rsatishda `XXXXX-XXXXX-XXXX` shaklida beriladi, shuning uchun
    solishtirishdan oldin ajratgichlar olib tashlanadi va katta harfga
    keltiriladi.
    """
    return "".join(ch for ch in (raw or "").upper() if ch in ALPHABET)


def generate() -> str:
    """Yangi kod yasaydi. `secrets` — kriptografik tasodifiy manba."""
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))


def pretty(code: str) -> str:
    """XXXXX-XXXXX-XXXX — qo'lda ko'chirish oson bo'lsin."""
    return "%s-%s-%s" % (code[:5], code[5:10], code[10:])


def set_code(code: str) -> None:
    """Kodni almashtiradi. Faqat BITTA kod amal qiladi — eskisi o'chadi.

    Kod SAQLASHDAN OLDIN ham `normalize()` dan o'tkaziladi. Bu shart:
    `verify()` kiruvchi qiymatni normalizatsiya qiladi, shuning uchun
    saqlashda qilinmasa ikkalasi bir-biriga mos kelmasdi — alifboga
    kirmaydigan belgi (masalan `I` yoki `O`) bilan qo'yilgan kodni keyin
    hech qachon tasdiqlab bo'lmasdi.
    """
    ensure_table()
    clean = normalize(code)
    if len(clean) != CODE_LEN:
        raise ValueError("Kod %d belgidan iborat bo'lishi kerak (alifbo: %s)"
                         % (CODE_LEN, ALPHABET))
    db.execute("DELETE FROM auth_codes")
    db.execute("INSERT INTO auth_codes (code_hash) VALUES (:h)",
               {"h": hash_password(clean)})


def clear_code() -> None:
    ensure_table()
    db.execute("DELETE FROM auth_codes")


def status() -> dict:
    """Kod bor-yo'qligi va sanalari. KODNING O'ZI hech qachon qaytarilmaydi."""
    ensure_table()
    row = db.fetch_one(
        "SELECT created_at, last_used_at FROM auth_codes ORDER BY id DESC LIMIT 1")
    if not row:
        return {"bor": False}
    return {
        "bor": True,
        "yaratilgan": _fmt(row["created_at"]),
        "oxirgi_ishlatilgan": _fmt(row["last_used_at"]),
    }


def verify(raw: str) -> bool:
    """Kod to'g'rimi. Kod o'rnatilmagan bo'lsa HAR DOIM False."""
    ensure_table()
    code = normalize(raw)
    if len(code) != CODE_LEN:
        return False

    row = db.fetch_one(
        "SELECT id, code_hash FROM auth_codes ORDER BY id DESC LIMIT 1")
    if not row:
        return False

    if not verify_password(code, row["code_hash"]):
        return False

    db.execute("UPDATE auth_codes SET last_used_at = NOW() WHERE id = :i",
               {"i": row["id"]})
    return True


def _fmt(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)
