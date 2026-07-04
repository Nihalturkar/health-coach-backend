import uuid
from sqlalchemy import Column, String, Boolean, Date, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date = Column(Date, nullable=False)
    weight_kg = Column(Numeric(5, 2), nullable=True)
    water_ml = Column(Integer, default=0)
    sleep_hours = Column(Numeric(3, 1), nullable=True)
    energy_level = Column(Integer, nullable=True)
    mood = Column(String(20), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    meal_name = Column(String(200), nullable=False)
    calories = Column(Integer, nullable=True)
    protein_g = Column(Numeric(5, 1), nullable=True)
    carbs_g = Column(Numeric(5, 1), nullable=True)
    fats_g = Column(Numeric(5, 1), nullable=True)
    photo_url = Column(String, nullable=True)
    is_from_plan = Column(Boolean, default=False)
    meal_plan_id = Column(UUID(as_uuid=True), ForeignKey("meal_plans.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date = Column(Date, nullable=False)
    workout_plan_id = Column(UUID(as_uuid=True), ForeignKey("workout_plans.id"), nullable=True)
    duration_min = Column(Integer, nullable=True)
    calories_burned = Column(Integer, nullable=True)
    completed_exercises = Column(Integer, nullable=True)
    total_exercises = Column(Integer, nullable=True)
    feeling = Column(String(20), nullable=True)
    skipped = Column(Boolean, default=False)
    skip_reason = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
