"""Favqulodda kirish kodi — Google ishlamay qolganda ikkinchi yo'l.

NIMA UCHUN KERAK
================
Sayt faqat Google orqali ochiladi. Bu odatda yaxshi, lekin egasini o'z
saytidan tashqarida qoldirib qo'yishi mumkin:
  - boshqa qurilmada Google akkaunti ochilmagan bo'lsa;
  - saytga boshqa domendan kirilsa (OAuth "Authorized origins" ro'yxatida
    bo'lmagan domenda Google tugmasi ishlamaydi);
  - Google xizmati vaqtincha ishlamasa.

Shu sabab 12 belgilik kod bilan ham kirish mumkin.

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

4. Kodni EGASI o'zi yozadi, tizim yasamaydi.

   Ilgari kod tasodifiy yasalardi va bir marta ko'rsatilardi. Amalda bu
   ishlamadi: tasodifiy kod eslab qolinmasdi va o'sha zahoti ko'chirib
   olinmasa butunlay yo'qolardi — ya'ni favqulodda yo'l aynan kerak
   bo'lgan paytda ochilmasdi. Eslab qoladigan kod — ishlaydigan kod.

   Buning evaziga kod tasodifiylikni yo'qotadi, shuning uchun ikki
   cheklov qo'yilgan: uzunligi ANIQ 12 belgi va kamida 5 xil belgi
   (ya'ni "AAAAAAAAAAAA" o'tmaydi). Ustiga kirish urinishlari IP bo'yicha
   cheklangan (`check_login_rate_limit`), shuning uchun taxmin qilib
   topish yo'li yopiq.

5. Kod XOTIRADA solishtiriladi (`bcrypt.checkpw`) — u doimiy vaqtda
   ishlaydi, ya'ni javob tezligiga qarab belgi taxmin qilib bo'lmaydi.
"""
from __future__ import annotations

from datetime import datetime

from . import db
from .security import hash_password, verify_password

CODE_LEN = 12
MIN_UNIQUE = 5   # "AAAAAAAAAAAA" kabi kodlar o'tmasin


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
    """Kodni solishtirishga tayyorlaydi.

    Faqat AJRATGICHLAR olib tashlanadi (bo'shliq, chiziqcha, pastki
    chiziq) va katta harfga keltiriladi. Boshqa hech narsa o'chirilmaydi.

    Ilgari bu yerda alifboga kirmagan HAR QANDAY belgi tashlab
    yuborilardi. Tizim yasagan kod uchun bu zararsiz edi, lekin kodni
    egasi yozadigan bo'lgach xavfli: odam "MENING-KODIM-01" deb yozsa,
    O va 0 jimgina o'chib, kod umuman boshqa narsaga aylanardi.

    `set_code()` ham, `verify()` ham AYNAN shu funksiyadan o'tadi —
    ikkalasi bir xil qoidaga bo'ysunmasa, o'rnatilgan kodni keyin
    hech qachon tasdiqlab bo'lmasdi.
    """
    text = (raw or "").upper()
    return "".join(ch for ch in text if ch not in " -_\t")


def set_code(code: str) -> None:
    """Egasi yozgan kodni o'rnatadi. Faqat BITTA kod amal qiladi.

    Kod SAQLASHDAN OLDIN ham `normalize()` dan o'tkaziladi — `verify()`
    ham shuni qiladi, ikkalasi mos kelishi shart.

    Ikki cheklov bor, ikkalasi ham ATAYLAB:
      - uzunlik ANIQ 12: bu kod Google'ni chetlab o'tadi, qisqasi
        yaramaydi;
      - kamida 5 xil belgi: "AAAAAAAAAAAA" yoki "121212121212" 12 belgi
        bo'lsa ham bir zumda taxmin qilinadi.
    """
    ensure_table()
    clean = normalize(code)
    if len(clean) != CODE_LEN:
        raise ValueError("Kod aniq %d belgidan iborat bo'lishi kerak "
                         "(hozir %d ta)." % (CODE_LEN, len(clean)))
    if len(set(clean)) < MIN_UNIQUE:
        raise ValueError("Kod juda oddiy: kamida %d xil belgi bo'lsin."
                         % MIN_UNIQUE)
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
