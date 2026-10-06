from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: RegisterRequest) -> TokenResponse:
        # Check if email already exists
        existing = await db.execute(
            select(User).where(User.email == data.email.lower().strip())
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu email bilan ro'yxatdan o'tilgan (Email already registered)",
            )

        hashed_password = get_password_hash(data.password)
        new_user = User(
            email=data.email.lower().strip(),
            password_hash=hashed_password,
            full_name=data.full_name.strip(),
            role=data.role,
            phone=data.phone.strip() if data.phone else None,
            is_active=True,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        access_token = create_access_token(
            subject=new_user.id, role=new_user.role.value, email=new_user.email
        )
        refresh_token = create_refresh_token(
            subject=new_user.id, role=new_user.role.value, email=new_user.email
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user),
        )

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
        result = await db.execute(
            select(User).where(
                User.email == email.lower().strip(), User.deleted_at.is_(None)
            )
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email yoki parol noto'g'ri (Invalid email or password)",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Foydalanuvchi hisobi bloklangan (Account inactive)",
            )

        access_token = create_access_token(
            subject=user.id, role=user.role.value, email=user.email
        )
        refresh_token = create_refresh_token(
            subject=user.id, role=user.role.value, email=user.email
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Yaroqsiz refresh token (Invalid refresh token)",
            )

        user_id = payload.get("sub")
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Foydalanuvchi topilmadi yoki bloklangan",
            )

        new_access_token = create_access_token(
            subject=user.id, role=user.role.value, email=user.email
        )
        new_refresh_token = create_refresh_token(
            subject=user.id, role=user.role.value, email=user.email
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
