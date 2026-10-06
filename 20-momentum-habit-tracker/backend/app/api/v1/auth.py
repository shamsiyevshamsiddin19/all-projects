from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserPasswordUpdate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi foydalanuvchini ro'yxatdan o'tkazish (Teacher yoki Student)",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.register(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Email va parol orqali tizimga kirish",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.login(db, data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Access tokenni yangilash (Refresh token)",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.refresh_access_token(db, data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Joriy kirgan foydalanuvchi ma'lumotlari",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    return UserResponse.model_validate(current_user)
