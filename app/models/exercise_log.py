import uuid
from sqlalchemy import Column, String, Date, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date = Column(Date, nullable=False)
    exercise_name = Column(String(200), nullable=False, index=True)
    muscle_group = Column(String(30), nullable=True)
    # Store each set as JSON: [{"set": 1, "reps": 10, "weight_kg": 20}, ...]
    sets_data = Column(JSONB, nullable=False)
    total_sets = Column(Integer, nullable=False)
    total_reps = Column(Integer, nullable=False)
    max_weight_kg = Column(Numeric(5, 1), nullable=True)
    total_volume_kg = Column(Numeric(8, 1), nullable=True)  # sum(reps * weight) across sets
    notes = Column(String, nullable=True)
    workout_plan_id = Column(UUID(as_uuid=True), ForeignKey("workout_plans.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
