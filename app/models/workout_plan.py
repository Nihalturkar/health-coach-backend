import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_number = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    workout_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    duration_min = Column(Integer, nullable=True)
    location = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_plan_id = Column(UUID(as_uuid=True), ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True)
    exercise_name = Column(String(200), nullable=False)
    sets = Column(Integer, nullable=True)
    reps = Column(String(20), nullable=True)
    rest_seconds = Column(Integer, nullable=True)
    suggested_weight_kg = Column(Numeric(5, 1), nullable=True)
    instructions = Column(String, nullable=True)
    gif_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    muscle_group = Column(String(30), nullable=True)
    equipment = Column(String(50), nullable=True)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
