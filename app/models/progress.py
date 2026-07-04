import uuid
from sqlalchemy import Column, String, Date, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class ProgressPhoto(Base):
    __tablename__ = "progress_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    photo_url = Column(String, nullable=False)
    photo_type = Column(String(20), nullable=True)
    week_number = Column(Integer, nullable=False)
    ai_analysis = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_weight = Column(Numeric(5, 2), nullable=True)
    end_weight = Column(Numeric(5, 2), nullable=True)
    avg_calories_consumed = Column(Integer, nullable=True)
    avg_protein_consumed = Column(Integer, nullable=True)
    avg_water_ml = Column(Integer, nullable=True)
    workouts_completed = Column(Integer, nullable=True)
    workouts_skipped = Column(Integer, nullable=True)
    avg_sleep_hours = Column(Numeric(3, 1), nullable=True)
    ai_summary = Column(String, nullable=True)
    ai_suggestions = Column(JSONB, nullable=True)
    plan_adjustments = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class BloodReport(Base):
    __tablename__ = "blood_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    report_url = Column(String, nullable=False)
    report_date = Column(Date, nullable=True)
    extracted_data = Column(JSONB, nullable=True)
    ai_analysis = Column(JSONB, nullable=True)
    ai_suggestions = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
