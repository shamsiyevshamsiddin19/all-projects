"""Autentifikatsiya — PHP `api_handle_auth_action` ekvivalenti (holat/xabar formatida)."""

from __future__ import annotations

import json
import re

from fastapi import Request

from .. import access_code, db
# Standart ruxsatlar YAGONA joyda turadi (`users.py`). Ilgari bu ro'yxat
# auth.py ichida 7 marta qo'lda takrorlangan edi — bittasini yangilab,
# qolganini unutish juda oson va xato jimgina yuzaga chiqardi.
from .users import DEFAULT_ALLOWED_SECTIONS
from ..config import settings
from ..errors import AuthError, auth_response
from ..google_auth import email_allowed, is_admin_email, verify_google_id_token
from ..security import (
    check_login_rate_limit,
    clear_login_rate_limit,
    hash_password,
    verify_password,
)
from .common import s

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def handle_auth_action(request: Request, payload: dict) -> "object":
    amal = s(payload.get("amal"))
    if amal == "":
        raise AuthError("So'rov noto'g'ri yuborilgan.")

    # Google-only rejimda parol yo'llari BUTUNLAY yopiladi. Frontendda tugmani
    # olib qo'yishning o'zi yetarli emas — API to'g'ridan-to'g'ri ham chaqiriladi.
    if amal in ("royxatdan_otish", "kirish") and _google_only():
        raise AuthError("Bu saytga faqat Google orqali kiriladi.")

    if amal == "royxatdan_otish":
        return _register(request, payload)
    if amal == "kirish":
        return _login(request, payload)
    if amal == "google_kirish":
        return _google_login(request, payload)
    if amal == "kod_bilan_kirish":
        return _code_login(request, payload)
    if amal == "kirish_kodi_holati":
        return _code_status(request)
    if amal == "kirish_kodi_ornatish":
        return _code_set(request, payload)
    if amal == "kirish_kodi_ochirish":
        return _code_clear(request)
    if amal == "mening_kodim_holati":
        return _my_code_status(request)
    if amal == "mening_kodim_ornatish":
        return _my_code_set(request, payload)
    if amal == "sessiya_tekshir":
        return _check_session(request)
    if amal == "chiqish":
        request.session.clear()
        return auth_response(True, "Tizimdan muvaffaqiyatli chiqildi.")

    raise AuthError("Noma'lum amal yuborildi.")


def _google_only() -> bool:
    return settings.AUTH_MODE == "google"


def _account_exists() -> bool:
    return db.fetch_one("SELECT id FROM doktorlar LIMIT 1") is not None


def _register(request: Request, payload: dict):
    # Bu shaxsiy sayt — faqat BIRINCHI akkaunt ochilishi mumkin. Aks holda himoya
    # ma'nosiz bo'lardi: begona odam ro'yxatdan o'tib, yozuv huquqini olib qo'yardi.
    if _account_exists():
        raise AuthError("Ro'yxatdan o'tish yopiq. Mavjud akkaunt bilan kiring.")

    ism = s(payload.get("ism"))
    email = s(payload.get("email"))
    parol = str(payload.get("parol") or "")

    if ism == "" or email == "" or parol == "":
        raise AuthError("Barcha maydonlarni to'ldiring.")
    if not EMAIL_RE.match(email):
        raise AuthError("Email noto'g'ri formatda.")
    if len(parol) < 6:
        raise AuthError("Parol kamida 6 ta belgidan iborat bo'lishi kerak.")

    if db.fetch_one("SELECT id FROM doktorlar WHERE email = :e LIMIT 1", {"e": email}):
        raise AuthError("Bu email allaqachon ro'yxatdan o'tgan.")

    doktor_id = db.execute_returning_id(
        "INSERT INTO doktorlar (ism, email, parol_hash, kirish_turi) VALUES (:i, :e, :h, 'oddiy')",
        {"i": ism, "e": email, "h": hash_password(parol)},
    )

    request.session["doktor_id"] = doktor_id
    request.session["doktor_ism"] = ism
    request.session["doktor_email"] = email

    return auth_response(True, "Muvaffaqiyatli ro'yxatdan o'tdingiz.", {
        "doktor_id": doktor_id,
        "doktor_ism": ism,
        "doktor_email": email,
    })


def _login(request: Request, payload: dict):
    email = s(payload.get("email"))
    parol = str(payload.get("parol") or "")

    if email == "" or parol == "":
        raise AuthError("Email va parolni kiriting.")

    check_login_rate_limit(request)

    doktor = db.fetch_one("SELECT * FROM doktorlar WHERE email = :e LIMIT 1", {"e": email})
    if not doktor:
        raise AuthError("Bunday foydalanuvchi topilmadi.")

    if (doktor.get("kirish_turi") or "") == "google" and not doktor.get("parol_hash"):
        raise AuthError("Bu akkaunt Google orqali ochilgan. Google bilan kiring.")

    if not verify_password(parol, doktor.get("parol_hash")):
        raise AuthError("Parol noto'g'ri.")

    clear_login_rate_limit(request)
    request.session["doktor_id"] = int(doktor["id"])
    request.session["doktor_ism"] = doktor["ism"]
    request.session["doktor_email"] = doktor["email"]

    return auth_response(True, "Tizimga muvaffaqiyatli kirildi.", {
        "doktor_id": int(doktor["id"]),
        "doktor_ism": doktor["ism"],
        "doktor_email": doktor["email"],
    })


def _google_login(request: Request, payload: dict):
    """Google orqali kirish — YAGONA ishonchli yo'l.

    Mijozdan faqat Google imzolagan ID token (`credential`) olinadi. Email
    TOKEN ICHIDAN chiqadi, mijoz yuborgan maydondan emas — aks holda uni
    istalgan odam o'zgartirib yuborardi.
    """
    check_login_rate_limit(request)

    # Google Identity Services `credential` deb yuboradi; eski nom ham qabul
    # qilinadi, lekin har ikkalasi ham TEKSHIRILADI.
    token = s(payload.get("credential")) or s(payload.get("id_token"))
    info = verify_google_id_token(token)

    email = info["email"]
    if not email_allowed(email):
        # Kim urinib ko'rgani jurnalda qolsin, lekin javobda tafsilot bermaymiz.
        raise AuthError("Bu akkauntga ruxsat yo'q.")

    ism = info["name"]
    sub = info["sub"]

    if is_admin_email(email):
        role = "admin"
        ruxsatlar = ["*"]
    else:
        role = "user"
        user_row = db.fetch_one(
            "SELECT * FROM foydalanuvchilar WHERE LOWER(email) = LOWER(:e) AND holat = 'faol' LIMIT 1",
            {"e": email},
        )
        if user_row:
            raw_r = user_row.get("ruxsatlar") or list(DEFAULT_ALLOWED_SECTIONS)
            if isinstance(raw_r, str):
                try:
                    ruxsatlar = json.loads(raw_r)
                except Exception:
                    ruxsatlar = list(DEFAULT_ALLOWED_SECTIONS)
            else:
                ruxsatlar = list(raw_r)
            if not user_row.get("ism") and ism:
                db.execute("UPDATE foydalanuvchilar SET ism = :i WHERE id = :id", {"i": ism, "id": user_row["id"]})
        else:
            ruxsatlar = list(DEFAULT_ALLOWED_SECTIONS)

    doktor = db.fetch_one("SELECT * FROM doktorlar WHERE email = :e LIMIT 1", {"e": email})

    if doktor:
        db.execute(
            "UPDATE doktorlar SET ism = :i, firebase_uid = :f, kirish_turi = 'google' WHERE id = :id",
            {"i": ism, "f": sub, "id": doktor["id"]},
        )
        doktor_id = int(doktor["id"])
    else:
        # Ruxsat etilgan email uchun akkaunt yo'q bo'lsa — ochib beramiz.
        doktor_id = db.execute_returning_id(
            "INSERT INTO doktorlar (ism, email, firebase_uid, kirish_turi) "
            "VALUES (:i, :e, :f, 'google')",
            {"i": ism, "e": email, "f": sub},
        )

    clear_login_rate_limit(request)
    request.session["doktor_id"] = doktor_id
    request.session["doktor_ism"] = ism
    request.session["doktor_email"] = email
    request.session["role"] = role
    request.session["ruxsatlar"] = ruxsatlar

    return auth_response(True, "Google orqali kirildi.", {
        "doktor_id": doktor_id,
        "doktor_ism": ism,
        "doktor_email": email,
        "role": role,
        "ruxsatlar": ruxsatlar,
    })


def _code_login(request: Request, payload: dict):
    """12 belgilik favqulodda kod bilan kirish.

    Google ishlamay qolganda egasi (admin) yoki ruxsat etilgan foydalanuvchilar
    o'z hisobiga maxfiy 12 talik kod orqali kira olsin.
    """
    check_login_rate_limit(request)

    raw_kod = s(payload.get("kod"))
    cleaned_code = re.sub(r"[^A-Za-z0-9]", "", raw_kod).upper()

    # 1. Admin favqulodda kodi tekshiruvi
    if access_code.verify(raw_kod) or (cleaned_code and access_code.verify(cleaned_code)):
        allowed = settings.ALLOWED_EMAILS
        if not allowed:
            raise AuthError("Ruxsat etilgan email sozlanmagan.")
        email = allowed[0]

        doktor = db.fetch_one("SELECT * FROM doktorlar WHERE email = :e LIMIT 1", {"e": email})
        if doktor:
            doktor_id = int(doktor["id"])
            ism = doktor["ism"] or "Egasi"
        else:
            ism = "Egasi"
            doktor_id = db.execute_returning_id(
                "INSERT INTO doktorlar (ism, email, kirish_turi) VALUES (:i, :e, 'kod')",
                {"i": ism, "e": email},
            )

        clear_login_rate_limit(request)
        request.session["doktor_id"] = doktor_id
        request.session["doktor_ism"] = ism
        request.session["doktor_email"] = email
        request.session["role"] = "admin"
        request.session["ruxsatlar"] = ["*"]

        return auth_response(True, "Kod bilan kirildi.", {
            "doktor_id": doktor_id,
            "doktor_ism": ism,
            "doktor_email": email,
            "role": "admin",
            "ruxsatlar": ["*"],
        })

    # 2. Foydalanuvchilar maxfiy 12 talik kodi tekshiruvi
    if cleaned_code and len(cleaned_code) == 12:
        try:
            users = db.fetch_all(
                "SELECT id, email, ism, ruxsatlar, holat, kirish_kodi "
                "FROM foydalanuvchilar WHERE holat = 'faol' AND kirish_kodi IS NOT NULL AND kirish_kodi != ''"
            )
            for u in users:
                if verify_password(cleaned_code, u.get("kirish_kodi")):
                    email = u["email"].strip().lower()
                    ism = (u.get("ism") or email.split("@")[0]).strip()
                    raw_r = u.get("ruxsatlar") or list(DEFAULT_ALLOWED_SECTIONS)
                    if isinstance(raw_r, str):
                        try:
                            ruxsatlar = json.loads(raw_r)
                        except Exception:
                            ruxsatlar = list(DEFAULT_ALLOWED_SECTIONS)
                    else:
                        ruxsatlar = list(raw_r)

                    doktor = db.fetch_one("SELECT * FROM doktorlar WHERE email = :e LIMIT 1", {"e": email})
                    if doktor:
                        doktor_id = int(doktor["id"])
                        db.execute(
                            "UPDATE doktorlar SET ism = :i, kirish_turi = 'kod' WHERE id = :id",
                            {"i": ism, "id": doktor_id},
                        )
                    else:
                        doktor_id = db.execute_returning_id(
                            "INSERT INTO doktorlar (ism, email, kirish_turi) VALUES (:i, :e, 'kod')",
                            {"i": ism, "e": email},
                        )

                    clear_login_rate_limit(request)
                    request.session["doktor_id"] = doktor_id
                    request.session["doktor_ism"] = ism
                    request.session["doktor_email"] = email
                    request.session["role"] = "user"
                    request.session["ruxsatlar"] = ruxsatlar

                    return auth_response(True, "Kod bilan kirildi.", {
                        "doktor_id": doktor_id,
                        "doktor_ism": ism,
                        "doktor_email": email,
                        "role": "user",
                        "ruxsatlar": ruxsatlar,
                    })
        except Exception:
            pass

    raise AuthError("Kod noto'g'ri.")



def _require_session(request: Request) -> None:
    """Kodni ko'rish/almashtirish faqat ICHKARIDAN. Aks holda istalgan
    odam yangi kod yasab, o'zi uchun kirish ochib olardi."""
    if not request.session.get("doktor_id"):
        raise AuthError("Bu amal uchun tizimga kirishingiz kerak.")


def _require_admin_session(request: Request) -> None:
    """Favqulodda kirish kodi — EGANING kodi, hammaning emas.

    2026-09-08 DA TOPILGAN TESHIK
    =============================
    Bu uchta amal faqat `_require_session()` bilan himoyalangan edi: "tizimga
    kirgan bo'lsa yetarli". Yagona foydalanuvchi paytida bu to'g'ri edi —
    kirgan odam eganing o'zi bo'lardi. Ko'p foydalanuvchi qo'shilgach tenglik
    BUZILDI: oddiy foydalanuvchi `kirish_kodi_ornatish` bilan kodni o'ziga
    almashtirib, keyin `kod_bilan_kirish` orqali `role="admin"`,
    `ruxsatlar=["*"]` sessiyasini ochib olardi — ya'ni to'liq egalik.

    Shuning uchun endi ROL tekshiriladi, shunchaki sessiya emas.
    """
    _require_session(request)
    email = (request.session.get("doktor_email") or "").strip().lower()
    if request.session.get("role") == "admin" or is_admin_email(email):
        return
    raise AuthError("Bu amal faqat sayt egasi uchun.")


def _code_status(request: Request):
    _require_admin_session(request)
    return auth_response(True, "Holat.", access_code.status())


def _code_set(request: Request, payload: dict):
    """Egasi YOZGAN kodni o'rnatadi.

    Ilgari kod tizim tomonidan yasalar va bir marta ko'rsatilardi. Amalda
    bu ishlamadi: tasodifiy kod eslab qolinmasdi va o'sha zahoti ko'chirib
    olinmasa yo'qolardi — favqulodda yo'l aynan kerak bo'lgan paytda
    ochilmasdi.

    Kod JAVOBDA QAYTARILMAYDI: uni foydalanuvchi o'zi yozgan, ya'ni
    biladi. Serverdan qaytarish faqat ortiqcha nusxa yaratardi.
    """
    _require_admin_session(request)
    try:
        access_code.set_code(s(payload.get("kod")))
    except ValueError as exc:
        raise AuthError(str(exc))
    return auth_response(True, "Kod o'rnatildi.", access_code.status())


def _code_clear(request: Request):
    _require_admin_session(request)
    access_code.clear_code()
    return auth_response(True, "Kod o'chirildi.", {"bor": False})


def _my_code_status(request: Request):
    """Foydalanuvchining O'Z akkaunt paroli holati.

    Yuqoridagi `_code_*` amallari EGANING favqulodda kodi bilan ishlaydi va
    admin talab qiladi. Bu esa boshqacha: har bir taklif qilingan
    foydalanuvchi `foydalanuvchilar.kirish_kodi` ustunidagi O'Z parolini
    ko'radi va o'zgartiradi — faqat o'zinikini.
    """
    _require_session(request)
    email = (request.session.get("doktor_email") or "").strip().lower()
    if request.session.get("role") == "admin" or is_admin_email(email):
        # Egada alohida akkaunt qatori yo'q — uning yo'li favqulodda kod.
        return auth_response(True, "Holat.", {"bor": False, "admin": True, "email": email})

    row = db.fetch_one(
        "SELECT (kirish_kodi IS NOT NULL AND kirish_kodi != '') AS bor, ism "
        "FROM foydalanuvchilar WHERE LOWER(email) = LOWER(:e) LIMIT 1",
        {"e": email},
    )
    if not row:
        raise AuthError("Akkaunt topilmadi.")
    return auth_response(True, "Holat.", {
        "bor": bool(row.get("bor")), "admin": False,
        "email": email, "ism": row.get("ism") or "",
    })


def _my_code_set(request: Request, payload: dict):
    """O'z akkaunt parolini o'rnatish/almashtirish.

    FAQAT o'zinikini: `WHERE email = <sessiyadagi email>`. Boshqa
    foydalanuvchining parolini bu yerdan o'zgartirib bo'lmaydi.
    """
    _require_session(request)
    email = (request.session.get("doktor_email") or "").strip().lower()
    if request.session.get("role") == "admin" or is_admin_email(email):
        raise AuthError("Egaga bu yo'l emas — favqulodda kirish kodidan foydalaning.")

    code = re.sub(r"[^A-Za-z0-9]", "", str(payload.get("kod") or "")).upper()
    if len(code) != 12:
        raise AuthError("Parol roppa-rosa 12 ta belgidan iborat bo'lishi kerak.")
    if len(set(code)) < 4:
        raise AuthError("Parol juda oddiy — kamida 4 xil belgi bo'lsin.")

    changed = db.execute(
        "UPDATE foydalanuvchilar SET kirish_kodi = :k, updated_at = CURRENT_TIMESTAMP "
        "WHERE LOWER(email) = LOWER(:e) AND holat = 'faol'",
        {"k": hash_password(code), "e": email},
    )
    if not changed:
        raise AuthError("Akkaunt topilmadi.")
    return auth_response(True, "Parol yangilandi.", {"bor": True})


def _check_session(request: Request):
    if request.session.get("doktor_id"):
        email = (request.session.get("doktor_email") or "").strip().lower()
        role = request.session.get("role")
        if not role:
            role = "admin" if is_admin_email(email) else "user"
            request.session["role"] = role

        if role != "admin":
            u = db.fetch_one(
                "SELECT * FROM foydalanuvchilar WHERE LOWER(email) = LOWER(:e) AND holat = 'faol' LIMIT 1",
                {"e": email},
            )
            if not u:
                request.session.clear()
                return auth_response(True, "Sessiya topilmadi.", {
                    "kirganmi": False,
                    "sozlanganmi": _account_exists(),
                    "himoya": bool(settings.REQUIRE_AUTH),
                    "kirish_usuli": "google" if _google_only() else "parol",
                    "google_client_id": settings.GOOGLE_CLIENT_ID if _google_only() else "",
                    "kod_bor": access_code.status().get("bor", False),
                })
            raw_r = u.get("ruxsatlar") or list(DEFAULT_ALLOWED_SECTIONS)
            if isinstance(raw_r, str):
                try:
                    ruxsatlar = json.loads(raw_r)
                except Exception:
                    ruxsatlar = list(DEFAULT_ALLOWED_SECTIONS)
            else:
                ruxsatlar = list(raw_r)
            request.session["ruxsatlar"] = ruxsatlar
        else:
            ruxsatlar = ["*"]

        return auth_response(True, "Sessiya faol.", {
            "kirganmi": True,
            "doktor_id": request.session.get("doktor_id"),
            "doktor_ism": request.session.get("doktor_ism", ""),
            "doktor_email": request.session.get("doktor_email", ""),
            "role": role,
            "ruxsatlar": ruxsatlar,
        })
    # `sozlanganmi=False` — hali birorta akkaunt yo'q, ya'ni ilk sozlash bosqichi.
    return auth_response(True, "Sessiya topilmadi.", {
        "kirganmi": False,
        "sozlanganmi": _account_exists(),
        "himoya": bool(settings.REQUIRE_AUTH),
        # Frontend shu ikkisiga qarab Google tugmasini chizadi.
        "kirish_usuli": "google" if _google_only() else "parol",
        "google_client_id": settings.GOOGLE_CLIENT_ID if _google_only() else "",
        # Kirish ekrani "Kod bilan kirish" havolasini FAQAT kod
        # o'rnatilgan bo'lsa ko'rsatadi — bo'lmasa u foydasiz tugma.
        "kod_bor": access_code.status().get("bor", False),
    })
