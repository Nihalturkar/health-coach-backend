from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    UpdateNotificationPreferenceRequest,
    FCMTokenRequest,
    MessageResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.get_notifications(
        db, str(current_user.id), page, limit, unread_only
    )


@router.put("/{notification_id}/read", response_model=MessageResponse)
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.mark_read(db, str(current_user.id), notification_id)


@router.put("/read-all", response_model=MessageResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.mark_all_read(db, str(current_user.id))


@router.get("/settings", response_model=NotificationPreferenceResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.get_preferences(db, str(current_user.id))


@router.put("/settings", response_model=NotificationPreferenceResponse)
async def update_settings(
    body: UpdateNotificationPreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    return await notification_service.update_preferences(db, str(current_user.id), data)


@router.post("/fcm-token", response_model=MessageResponse)
async def update_fcm_token(
    body: FCMTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.update_fcm_token(db, str(current_user.id), body.fcm_token)
