"""Egalik (owner) konteksti.

Bu ilova login talab qilmaydi — barcha foydalanuvchilar bitta umumiy ('global','shared')
fazoda ishlaydi. Shu sababli owner_context har doim umumiy kontekstni qaytaradi va
autentifikatsiyaga bog'liq ma'lumot chegarasi (account-takeover xavfi) yo'q.
"""

from __future__ import annotations

from fastapi import Request

SHARED_OWNER_TYPE = "global"
SHARED_OWNER_KEY = "shared"


def owner_context(request: Request) -> dict[str, str]:
    return {"owner_type": SHARED_OWNER_TYPE, "owner_key": SHARED_OWNER_KEY}


def global_context() -> dict[str, str]:
    return {"owner_type": "global", "owner_key": "site"}


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get("doktor_id"))
