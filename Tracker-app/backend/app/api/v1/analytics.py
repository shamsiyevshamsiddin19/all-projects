from typing import Any, Dict, Optional, Union
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    get_db,
    require_teacher,
)
from app.exports.excel_generator import generate_excel_report
from app.exports.pdf_generator import generate_pdf_report
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.analytics import StudentDashboardStats, TeacherDashboardStats
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])


@router.get(
    "/dashboard",
    response_model=Union[TeacherDashboardStats, StudentDashboardStats],
    summary="Foydalanuvchi roli bo'yicha Dashboard ko'rsatkichlari",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if current_user.role == UserRole.TEACHER:
        return await AnalyticsService.get_teacher_stats(db, current_user)
    else:
        return await AnalyticsService.get_student_stats(db, current_user)


@router.get(
    "/export/pdf",
    summary="Hisobotni professional PDF formatda yuklab olish (O'qituvchi)",
)
async def export_pdf_report(
    group_id: Optional[str] = Query(None, description="Aniq bir guruh ID si (ixtiyoriy)"),
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    report_data = await AnalyticsService.get_report_data(db, teacher, group_id)
    pdf_buffer = generate_pdf_report(
        title=report_data["title"],
        teacher_name=report_data["teacher_name"],
        target_name=report_data["target_name"],
        report_type=report_data["report_type"],
        stats=report_data["stats"],
        items=report_data["items"],
    )

    filename = f"Tracker_Report_{datetime_now_str()}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/export/excel",
    summary="Hisobotni tuzilgan Excel (XLSX) formatda yuklab olish (O'qituvchi)",
)
async def export_excel_report(
    group_id: Optional[str] = Query(None, description="Aniq bir guruh ID si (ixtiyoriy)"),
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    report_data = await AnalyticsService.get_report_data(db, teacher, group_id)
    excel_buffer = generate_excel_report(
        title=report_data["title"],
        teacher_name=report_data["teacher_name"],
        target_name=report_data["target_name"],
        report_type=report_data["report_type"],
        stats=report_data["stats"],
        items=report_data["items"],
    )

    filename = f"Tracker_Report_{datetime_now_str()}.xlsx"
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def datetime_now_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")
