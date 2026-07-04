from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    data: Optional[Any]
    is_read: bool
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    page: int
    limit: int


class NotificationPreferenceResponse(BaseModel):
    meal_reminders: bool
    meal_reminder_times: Optional[Any]
    workout_reminders: bool
    workout_reminder_time: Optional[str]
    water_reminders: bool
    water_reminder_interval_hours: int
    weigh_in_reminder: bool
    weigh_in_time: Optional[str]
    weekly_review_notification: bool
    achievement_notifications: bool
    tip_notifications: bool
    fcm_token: Optional[str]

    class Config:
        from_attributes = True


class UpdateNotificationPreferenceRequest(BaseModel):
    meal_reminders: Optional[bool] = None
    meal_reminder_times: Optional[List[str]] = None
    workout_reminders: Optional[bool] = None
    workout_reminder_time: Optional[str] = None
    water_reminders: Optional[bool] = None
    water_reminder_interval_hours: Optional[int] = None
    weigh_in_reminder: Optional[bool] = None
    weigh_in_time: Optional[str] = None
    weekly_review_notification: Optional[bool] = None
    achievement_notifications: Optional[bool] = None
    tip_notifications: Optional[bool] = None


class FCMTokenRequest(BaseModel):
    fcm_token: str


class MessageResponse(BaseModel):
    message: str
