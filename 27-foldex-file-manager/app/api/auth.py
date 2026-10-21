# -*- coding: utf-8 -*-
"""
Foldex Autentifikatsiya API yo'llari (Auth API).
Telegram Mini App (WebApp) initData, botdagi bir martalik /login tokenlari,
sessiyani tekshirish va tizimdan chiqish (logout) amallarini boshqaradi.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_telegram_webapp_data
from app.models.auth_token import AdminAuthToken
from app.schemas.auth import AdminUserOut, TokenAuthRequest, TokenResponse, WebAppAuthRequest

router = APIRouter(prefix="/api/auth", tags=["Autentifikatsiya"])


@router.post("/webapp", response_model=TokenResponse)
async def login_via_webapp(
    payload: WebAppAuthRequest,
    response: Response
):
    """
    Telegram Mini App (WebApp) dan yuborilgan initData ni tekshirish.
    Telegram kriptografik imzosi to'g'ri bo'lsa va foydalanuvchi ID si
    7883409434 bo'lsa, JWT token yaratadi va HTTPOnly Cookie ga joylaydi.
    """
    user_data = verify_telegram_webapp_data(payload.init_data)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram autentifikatsiyasi tasdiqlanmadi yoki ruxsat yo'q!"
        )

    user_id = user_data["id"]
    token = create_access_token(data={"sub": str(user_id), "role": "admin"})

    # Xavfsiz HTTPOnly cookie o'rnatish
    response.set_cookie(
        key="foldex_token",
        value=token,
        httponly=True,
        secure=settings.DOMAIN.startswith("https"),
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS * 86400
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user_id,
        first_name=user_data.get("first_name"),
        username=user_data.get("username")
    )


@router.post("/verify-token", response_model=TokenResponse)
async def verify_one_time_token(
    payload: TokenAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Botdagi /login komandasi bergan bir martalik xavfsiz tokenni tekshirish (JSON API orqali).
    """
    stmt = select(AdminAuthToken).where(
        AdminAuthToken.token == payload.token,
        AdminAuthToken.is_used == False
    )
    res = await db.execute(stmt)
    token_obj = res.scalar_one_or_none()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bir martalik token noto'g'ri yoki allaqachon ishlatilgan!"
        )

    # Amal qilish muddatini tekshirish
    if datetime.now(timezone.utc) > token_obj.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tokenning amal qilish muddati tugagan! Botdan qaytadan /login oling."
        )

    # Faqat 7883409434
    if token_obj.telegram_user_id != settings.TELEGRAM_ADMIN_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ruxsatsiz foydalanuvchi!"
        )

    # Tokenni ishlatilgan deb belgilash
    token_obj.is_used = True
    await db.commit()

    token = create_access_token(data={"sub": str(token_obj.telegram_user_id), "role": "admin"})

    response.set_cookie(
        key="foldex_token",
        value=token,
        httponly=True,
        secure=settings.DOMAIN.startswith("https"),
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS * 86400
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=token_obj.telegram_user_id
    )


@router.get("/me", response_model=AdminUserOut)
async def get_current_admin_info(
    admin_id: int = Depends(get_current_admin)
):
    """Joriy tizimga kirgan administrator profilini tekshirish."""
    return AdminUserOut(
        user_id=admin_id,
        is_admin=True,
        project_name=settings.PROJECT_NAME,
        domain=settings.DOMAIN
    )


@router.post("/logout")
async def logout(response: Response):
    """Tizimdan chiqish: Cookie ni tozalaydi."""
    response.delete_cookie(key="foldex_token")
    return {"success": True, "message": "Tizimdan muvaffaqiyatli chiqildi."}
