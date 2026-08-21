import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class MealFeedback(Base):
    __tablename__ = "meal_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_plan_id = Column(UUID(as_uuid=True), ForeignKey("meal_plans.id", ondelete="CASCADE"))
    meal_name = Column(String(200), nullable=False)
    meal_type = Column(String(20), nullable=False)
    rating = Column(Integer, nullable=False)  # 1=dislike, 2=ok, 3=liked
    reason = Column(String, nullable=True)  # "too_bland", "too_spicy", "don't_like_ingredient", etc.
    created_at = Column(DateTime, server_default=func.now())


class ExerciseFeedback(Base):
    __tablename__ = "exercise_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_name = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)  # "too_easy", "just_right", "too_hard", "painful"
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
