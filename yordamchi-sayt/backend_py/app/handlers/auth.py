"""Autentifikatsiya — PHP `api_handle_auth_action` ekvivalenti (holat/xabar formatida)."""

from __future__ import annotations

import re

from fastapi import Request

from .. import access_code, db
from ..config import settings
from ..errors import AuthError, auth_response
from ..google_auth import email_allowed, verify_google_id_token
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
    if amal == "kirish_kodi_yangilash":
        return _code_renew(request)
    if amal == "kirish_kodi_ochirish":
        return _code_clear(request)
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

    doktor = db.fetch_one("SELECT * FROM doktorlar WHERE email = :e LIMIT 1", {"e": email})

    if doktor:
        db.execute(
            "UPDATE doktorlar SET ism = :i, firebase_uid = :f, kirish_turi = 'google' WHERE id = :id",
            {"i": ism, "f": sub, "id": doktor["id"]},
        )
        doktor_id = int(doktor["id"])
    else:
        # Ruxsat etilgan email uchun akkaunt yo'q bo'lsa — ochib beramiz.
        # `_account_exists()` bu yerda TO'SIQ QILINMAYDI: aks holda bazadagi
        # eski akkaunt boshqa email bilan yozilgan bo'lsa, egasi o'z saytiga
        # kira olmay qolardi. Ma'lumot `owner_context` bo'yicha umumiy
        # fazoda saqlanadi, ya'ni yangi qator ochilishi hech narsani
        # yo'qotmaydi.
        doktor_id = db.execute_returning_id(
            "INSERT INTO doktorlar (ism, email, firebase_uid, kirish_turi) "
            "VALUES (:i, :e, :f, 'google')",
            {"i": ism, "e": email, "f": sub},
        )

    clear_login_rate_limit(request)
    request.session["doktor_id"] = doktor_id
    request.session["doktor_ism"] = ism
    request.session["doktor_email"] = email

    return auth_response(True, "Google orqali kirildi.", {
        "doktor_id": doktor_id,
        "doktor_ism": ism,
        "doktor_email": email,
    })


def _code_login(request: Request, payload: dict):
    """14 belgilik favqulodda kod bilan kirish.

    Google ishlamay qolganda (boshqa qurilma, boshqa domen, xizmat uzilishi)
    egasi o'z saytiga kira olsin. Kod O'RNATILMAGAN bo'lsa bu yo'l yopiq —
    ya'ni xususiyat o'zicha teshik ochmaydi.
    """
    check_login_rate_limit(request)

    if not access_code.verify(s(payload.get("kod"))):
        # Sabab aytilmaydi: "kod yo'q" va "kod noto'g'ri" bir xil javob
        # beradi, aks holda kod o'rnatilgan-o'rnatilmagani bilinib qolardi.
        raise AuthError("Kod noto'g'ri.")

    # Kod egaga tegishli, ya'ni ruxsat etilgan birinchi email akkauntiga
    # kiritamiz. Akkaunt bo'lmasa ochib beramiz — Google yo'lidagi kabi.
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

    return auth_response(True, "Kod bilan kirildi.", {
        "doktor_id": doktor_id,
        "doktor_ism": ism,
        "doktor_email": email,
    })


def _require_session(request: Request) -> None:
    """Kodni ko'rish/almashtirish faqat ICHKARIDAN. Aks holda istalgan
    odam yangi kod yasab, o'zi uchun kirish ochib olardi."""
    if not request.session.get("doktor_id"):
        raise AuthError("Bu amal uchun tizimga kirishingiz kerak.")


def _code_status(request: Request):
    _require_session(request)
    return auth_response(True, "Holat.", access_code.status())


def _code_renew(request: Request):
    """Yangi kod yasaydi va uni BIR MARTA qaytaradi.

    Keyin faqat xeshi qoladi — shuning uchun javobdagi kodni saqlab
    qo'yish kerak, u boshqa ko'rsatilmaydi."""
    _require_session(request)
    code = access_code.generate()
    access_code.set_code(code)
    data = access_code.status()
    data["kod"] = access_code.pretty(code)
    return auth_response(True, "Yangi kod yaratildi.", data)


def _code_clear(request: Request):
    _require_session(request)
    access_code.clear_code()
    return auth_response(True, "Kod o'chirildi.", {"bor": False})


def _check_session(request: Request):
    if request.session.get("doktor_id"):
        return auth_response(True, "Sessiya faol.", {
            "kirganmi": True,
            "doktor_id": request.session.get("doktor_id"),
            "doktor_ism": request.session.get("doktor_ism", ""),
            "doktor_email": request.session.get("doktor_email", ""),
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
