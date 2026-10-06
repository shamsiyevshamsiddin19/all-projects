from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    get_db,
    require_teacher,
)
from app.models.enums import AssignmentPriority
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentDetailResponse,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.auth import MessageResponse
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi vazifa yaratish (Faqat O'qituvchi)",
)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    return await AssignmentService.create_assignment(db, data, teacher)


@router.get(
    "",
    response_model=List[AssignmentResponse],
    summary="Vazifalar ro'yxati (Filtr, qidiruv va saralash bilan)",
)
async def list_assignments(
    group_id: Optional[str] = Query(None, description="Guruh bo'yicha filter"),
    priority: Optional[AssignmentPriority] = Query(None, description="Ustuvorlik bo'yicha filter"),
    search: Optional[str] = Query(None, description="Mavzu yoki tavsif bo'yicha qidiruv"),
    filter_status: Optional[str] = Query(None, description="active, completed, overdue, all"),
    sort_by: str = Query("newest", description="newest, oldest, deadline, priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await AssignmentService.list_assignments(
        db, current_user, group_id, priority, search, filter_status, sort_by, skip, limit
    )


@router.get(
    "/{assignment_id}",
    response_model=AssignmentDetailResponse,
    summary="Vazifa tafsilotlari",
)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await AssignmentService.get_assignment_detail(db, assignment_id, current_user)


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Vazifani tahrirlash (O'qituvchi)",
)
async def update_assignment(
    assignment_id: str,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    return await AssignmentService.update_assignment(db, assignment_id, data, teacher)


@router.delete(
    "/{assignment_id}",
    response_model=MessageResponse,
    summary="Vazifani o'chirish (O'qituvchi)",
)
async def delete_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    await AssignmentService.delete_assignment(db, assignment_id, teacher)
    return MessageResponse(message="Vazifa muvaffaqiyatli o'chirildi")
