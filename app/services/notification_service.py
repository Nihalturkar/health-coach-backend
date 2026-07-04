from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from fastapi import HTTPException, status

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference


async def get_notifications(
    db: AsyncSession, user_id: str, page: int, limit: int, unread_only: bool
) -> dict:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc())

    count_result = await db.execute(
        select(func.count()).select_from(
            select(Notification).where(Notification.user_id == user_id).subquery()
        )
    )
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return {
        "notifications": list(notifications),
        "total": total,
        "page": page,
        "limit": limit,
    }


async def mark_read(db: AsyncSession, user_id: str, notification_id: str) -> dict:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    return {"message": "Marked as read"}


async def mark_all_read(db: AsyncSession, user_id: str) -> dict:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}


async def get_preferences(db: AsyncSession, user_id: str) -> NotificationPreference:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        # Create default preferences
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs


async def update_preferences(db: AsyncSession, user_id: str, data: dict) -> NotificationPreference:
    prefs = await get_preferences(db, user_id)
    for key, value in data.items():
        if value is not None:
            setattr(prefs, key, value)
    await db.commit()
    await db.refresh(prefs)
    return prefs


async def update_fcm_token(db: AsyncSession, user_id: str, fcm_token: str) -> dict:
    prefs = await get_preferences(db, user_id)
    prefs.fcm_token = fcm_token
    await db.commit()
    return {"message": "FCM token updated"}
