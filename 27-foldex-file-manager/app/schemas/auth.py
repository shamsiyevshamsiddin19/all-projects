# -*- coding: utf-8 -*-
"""
Foldex Autentifikatsiya Pydantic sxemalari.
Telegram WebApp initData, bot bir martalik tokenlari va
admin sessiyasi javoblari uchun xizmat qiladi.
"""

from typing import Optional
from pydantic import BaseModel, Field


class WebAppAuthRequest(BaseModel):
    """Telegram Mini App (WebApp) orqali kirish so'rovi."""
    init_data: str = Field(..., description="Telegram WebApp initData qatori")


class TokenAuthRequest(BaseModel):
    """Botdagi /login komandasi orqali berilgan token bilan kirish."""
    token: str = Field(..., description="Bir martalik maxfiy token")


class TokenResponse(BaseModel):
    """Muvaffaqiyatli autentifikatsiya javobi."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    first_name: Optional[str] = None
    username: Optional[str] = None


class AdminUserOut(BaseModel):
    """Joriy tizimga kirgan administrator ma'lumotlari."""
    user_id: int
    is_admin: bool = True
    project_name: str
    domain: str
