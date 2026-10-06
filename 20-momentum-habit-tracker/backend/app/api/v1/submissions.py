from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    get_db,
    require_student,
    require_teacher,
)
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.schemas.submission import SubmissionCreate, SubmissionResponse
from app.services.submission_service import SubmissionService

router = APIRouter(tags=["Submissions & Grading"])


@router.post(
    "/assignments/{assignment_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vazifaga javob va fayllar topshirish (Talaba)",
)
async def submit_assignment(
    assignment_id: str,
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_student),
):
    return await SubmissionService.submit_assignment(db, assignment_id, data, student)


@router.get(
    "/assignments/{assignment_id}/submissions",
    response_model=List[SubmissionResponse],
    summary="Vazifa bo'yicha barcha topshirilgan ishlar (O'qituvchi)",
)
async def list_submissions_for_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    return await SubmissionService.list_assignment_submissions(db, assignment_id, teacher)


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionResponse,
    summary="Topshiriq ishi tafsilotlari",
)
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await SubmissionService.get_submission_detail(db, submission_id, current_user)


@router.post(
    "/submissions/{submission_id}/review",
    response_model=SubmissionResponse,
    summary="Topshiriqni baholash va feedback berish (O'qituvchi)",
)
async def review_submission(
    submission_id: str,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    return await SubmissionService.review_submission(db, submission_id, data, teacher)
