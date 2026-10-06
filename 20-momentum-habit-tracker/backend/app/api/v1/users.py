from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db, require_teacher
from app.core.security import get_password_hash, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import UserPasswordUpdate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users & Profile"])


@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Shaxsiy profil ma'lumotlarini tahrirlash",
)
async def update_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name.strip()
    if data.phone is not None:
        current_user.phone = data.phone.strip()
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url.strip()

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Parolni o'zgartirish",
)
async def change_password(
    data: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Joriy parol noto'g'ri (Current password incorrect)",
        )

    current_user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    return MessageResponse(message="Parol muvaffaqiyatli o'zgartirildi")


@router.get(
    "/students",
    response_model=List[UserResponse],
    summary="Talabalar ro'yxatini qidirish (Faqat o'qituvchilar uchun)",
)
async def list_students(
    search: Optional[str] = Query(None, description="Ism yoki email bo'yicha qidiruv"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    query = select(User).where(
        User.role == UserRole.STUDENT,
        User.is_active == True,
        User.deleted_at.is_(None),
    )
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()
    return [UserResponse.model_validate(s) for s in students]
