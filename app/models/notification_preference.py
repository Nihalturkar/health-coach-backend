import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    meal_reminders = Column(Boolean, default=True)
    meal_reminder_times = Column(JSONB, default=["08:00", "13:00", "20:00"])
    workout_reminders = Column(Boolean, default=True)
    workout_reminder_time = Column(String(5), default="07:00")
    water_reminders = Column(Boolean, default=True)
    water_reminder_interval_hours = Column(Integer, default=2)
    weigh_in_reminder = Column(Boolean, default=True)
    weigh_in_time = Column(String(5), default="07:30")
    weekly_review_notification = Column(Boolean, default=True)
    achievement_notifications = Column(Boolean, default=True)
    tip_notifications = Column(Boolean, default=True)
    fcm_token = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
