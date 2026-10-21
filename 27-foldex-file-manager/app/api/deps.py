# -*- coding: utf-8 -*-
"""
FastAPI bog'liqliklar (Dependencies) moduli.
Ma'lumotlar bazasi sessiyasini taqdim etadi va har bir API so'rovida
qat'iy ravishda TELEGRAM_ADMIN_ID (7883409434) huquqini tekshiradi.
"""

from typing import Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token


async def get_current_admin(
    request: Request,
    authorization: Optional[str] = Header(None),
    foldex_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> int:
    """
    Qat'iy xavfsizlik tekshiruvi:
    1. So'rovdan JWT tokenni (Cookie yoki Authorization: Bearer headeridan) qidiradi.
    2. Tokenni imzosini va yaroqlilik muddatini tekshiradi.
    3. Token ichidagi Telegram ID faqat va faqat settings.TELEGRAM_ADMIN_ID (7883409434)
       bilan teng bo'lishini tekshiradi.
    4. Agar mos kelmasa, HTTP 401 Unauthorized xatoligini qaytaradi.
    """
    token = None

    # a) Headerdan tokenni ajratib olish
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # b) Agar headerda bo'lmasa, HTTPOnly Cookie dan olish
    elif foldex_token:
        token = foldex_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tizimga kirilmagan! Avval Telegram orqali autentifikatsiyadan o'ting.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yaroqsiz yoki eskirgan sessiya tokeni!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = int(payload.get("sub", 0))
    if user_id != settings.TELEGRAM_ADMIN_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kirish taqiqlangan! Siz administrator emassiz."
        )

    return user_id


async def get_admin_optional(
    request: Request,
    foldex_token: Optional[str] = Cookie(None)
) -> Optional[int]:
    """
    HTML sahifalar (masalan bosh sahifa) uchun ixtiyoriy tekshiruv.
    Foydalanuvchi tizimga kirgan bo'lsa uning ID sini, aks holda None qaytaradi.
    """
    if not foldex_token:
        return None

    payload = decode_access_token(foldex_token)
    if not payload:
        return None

    user_id = int(payload.get("sub", 0))
    if user_id == settings.TELEGRAM_ADMIN_ID:
        return user_id

    return None
