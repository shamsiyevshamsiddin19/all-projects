from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="Foydalanuvchi bildirishnomalari",
)
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    notifs = result.scalars().all()
    return [NotificationResponse.model_validate(n) for n in notifs]


@router.patch(
    "/{notification_id}/read",
    response_model=MessageResponse,
    summary="Bildirishnomani o'qilgan deb belgilash",
)
async def mark_notification_as_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await db.execute(
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .values(is_read=True)
    )
    await db.commit()
    return MessageResponse(message="Bildirishnoma o'qildi deb belgilandi")


@router.patch(
    "/read-all",
    response_model=MessageResponse,
    summary="Barcha bildirishnomalarni o'qilgan deb belgilash",
)
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return MessageResponse(message="Barcha bildirishnomalar o'qilgan deb belgilandi")
