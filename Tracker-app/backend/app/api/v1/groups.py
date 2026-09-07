from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    get_db,
    require_student,
    require_teacher,
)
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.group import (
    AddStudentRequest,
    GroupCreate,
    GroupDetailResponse,
    GroupResponse,
    GroupUpdate,
    JoinGroupRequest,
)
from app.services.group_service import GroupService

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi guruh yaratish (Faqat O'qituvchi)",
)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    return await GroupService.create_group(db, data, teacher)


@router.get(
    "",
    response_model=List[GroupResponse],
    summary="Foydalanuvchining barcha guruhlari ro'yxati",
)
async def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await GroupService.get_user_groups(db, current_user, skip, limit)


@router.post(
    "/join",
    response_model=GroupDetailResponse,
    summary="Guruhga taklif kodi orqali qo'shilish (Talaba)",
)
async def join_group(
    data: JoinGroupRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
):
    return await GroupService.join_group_by_code(db, data.invite_code, student)


@router.get(
    "/{group_id}",
    response_model=GroupDetailResponse,
    summary="Guruh tafsilotlari va a'zolari",
)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await GroupService.get_group_detail(db, group_id, current_user)


@router.patch(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Guruh ma'lumotlarini tahrirlash (O'qituvchi)",
)
async def update_group(
    group_id: str,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    return await GroupService.update_group(db, group_id, data, teacher)


@router.delete(
    "/{group_id}",
    response_model=MessageResponse,
    summary="Guruhni o'chirish (O'qituvchi)",
)
async def delete_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    await GroupService.delete_group(db, group_id, teacher)
    return MessageResponse(message="Guruh muvaffaqiyatli o'chirildi")


@router.post(
    "/{group_id}/students",
    response_model=MessageResponse,
    summary="Guruhga talaba qo'shish (O'qituvchi)",
)
async def add_student(
    group_id: str,
    data: AddStudentRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    await GroupService.add_student_to_group(db, group_id, data.student_id, teacher)
    return MessageResponse(message="Talaba guruhga muvaffaqiyatli qo'shildi")


@router.delete(
    "/{group_id}/students/{student_id}",
    response_model=MessageResponse,
    summary="Talabani guruhdan chiqarish (O'qituvchi)",
)
async def remove_student(
    group_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    await GroupService.remove_student_from_group(db, group_id, student_id, teacher)
    return MessageResponse(message="Talaba guruhdan chiqarildi")
