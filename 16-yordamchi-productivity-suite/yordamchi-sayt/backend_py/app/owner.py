"""Egalik (owner) konteksti.

Har bir foydalanuvchi (admin yoki taklif qilingan foydalanuvchi) o'zining
shaxsiy xotira maydoniga ega (owner_type='user', owner_key=email).
Bu orqali "o'qidim", "yodlangan", "saqlangan" so'zlar va darslik belgilari
foydalanuvchilar o'rtasida chalkashib ketmaydi.
"""

from __future__ import annotations

from fastapi import Request

SHARED_OWNER_TYPE = "global"
SHARED_OWNER_KEY = "shared"

_SEEDED_USERS: set[str] = set()


def _ensure_user_storage_seeded(email: str) -> None:
    """Admin birinchi marta kirganda eski `global|shared` ma'lumotini ko'chiradi.

    2026-09-08 DA TOPILGAN NUQSON
    =============================
    Bu yerda `db.fetch_val` yozilgan edi — `db.py` da bunday funksiya YO'Q,
    u `fetch_value`. Chaqiruv `AttributeError` berardi, uni pastdagi
    `except Exception: pass` JIMGINA yutardi. Natijada ko'chirish HECH QACHON
    ishlamadi va sessiyada email paydo bo'lishi bilan ism, bio, avatar,
    maqsadlar, mavzular — hammasi yo'q bo'lib ko'rindi (ma'lumot esa
    `global|shared` da turgan edi).

    Ikki saboq: (1) `except: pass` xatoni ko'rinmas qiladi — endi log yoziladi;
    (2) bu funksiya faqat `app_storage` ni qamraydi, `language_topics`,
    `goals`, `sport_exercises` va boshqalarni EMAS. Ular 2026-09-08 da qo'lda
    ko'chirildi.
    """
    if not email or email in _SEEDED_USERS:
        return
    _SEEDED_USERS.add(email)
    try:
        from . import db
        from .config import settings

        if email in settings.ALLOWED_EMAILS:
            count = (
                db.fetch_value(
                    "SELECT COUNT(*) FROM app_storage WHERE owner_type = 'user' AND owner_key = :e",
                    {"e": email},
                )
                or 0
            )
            if count == 0:
                # Admin foydalanuvchining mavjud ma'lumotlarini yo'qotmaslik uchun
                # eski ('global', 'shared') dan shaxsiy hisobiga ko'chirib o'tkazamiz
                db.execute(
                    """
                    INSERT INTO app_storage (owner_type, owner_key, storage_key, storage_value)
                    SELECT 'user', :e, storage_key, storage_value
                    FROM app_storage
                    WHERE owner_type = 'global' AND owner_key = 'shared'
                    ON CONFLICT (owner_type, owner_key, storage_key) DO NOTHING
                    """,
                    {"e": email},
                )
    except Exception:  # noqa: BLE001
        # ATAYLAB yutilmaydi: aynan shu `pass` yuqoridagi typoni bir necha
        # kun ko'rinmas qilib turdi. Ko'chirish bo'lmasa ham ilova ishlashi
        # kerak, lekin sabab logda qolsin.
        import logging

        logging.getLogger("yordamchi").exception(
            "Foydalanuvchi xotirasini ko'chirib bo'lmadi (email=%s)", email
        )


def owner_context(request: Request) -> dict[str, str]:
    email = (request.session.get("doktor_email") or "").strip().lower()
    if email:
        _ensure_user_storage_seeded(email)
        return {"owner_type": "user", "owner_key": email}
    return {"owner_type": SHARED_OWNER_TYPE, "owner_key": SHARED_OWNER_KEY}


def admin_owner_context() -> dict[str, str]:
    """Admin egasining owner konteksti.

    User'lar admin qo'shgan kontentni (mavzular, materiallar) O'QISH uchun
    shu kontekstdan foydalanadi. Yozish/tahrirlash uchun EMAS — u handler
    darajasida `_require_admin()` bilan bloklangan.
    """
    from .config import settings

    admin_email = (settings.ALLOWED_EMAILS[0] if settings.ALLOWED_EMAILS else "").strip().lower()
    if admin_email:
        return {"owner_type": "user", "owner_key": admin_email}
    return {"owner_type": SHARED_OWNER_TYPE, "owner_key": SHARED_OWNER_KEY}


def content_read_context(request: Request) -> dict[str, str]:
    """Kontentni O'QISH uchun kontekst.

    Admin bo'lsa — o'z kontekstidan o'qiydi (odatdagidek).
    User bo'lsa — admin kontekstidan o'qiydi (admin qo'shgan darsliklarni ko'radi).
    Shaxsiy progresslar (o'qidim, yodladim, test natijalari) bu yerdan O'TMAYDI —
    ular `owner_context()` orqali har bir foydalanuvchining o'z hisobida qoladi.
    """
    from .config import settings
    from .google_auth import is_admin_email

    email = (request.session.get("doktor_email") or "").strip().lower()
    role = request.session.get("role")

    # Admin yoki sessiya yo'q — odatdagi kontekst
    if role == "admin" or is_admin_email(email):
        return owner_context(request)

    # User — admin kontentini o'qiydi
    return admin_owner_context()


def global_context() -> dict[str, str]:
    return {"owner_type": "global", "owner_key": "site"}


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get("doktor_id"))
