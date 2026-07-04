import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_number = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    meal_type = Column(String(20), nullable=False)
    meal_name = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    recipe = Column(String, nullable=True)
    ingredients = Column(JSONB, nullable=True)
    calories = Column(Integer, nullable=False)
    protein_g = Column(Numeric(5, 1), nullable=True)
    carbs_g = Column(Numeric(5, 1), nullable=True)
    fats_g = Column(Numeric(5, 1), nullable=True)
    fiber_g = Column(Numeric(5, 1), nullable=True)
    prep_time_min = Column(Integer, nullable=True)
    is_alternative = Column(Boolean, default=False)
    alternative_for = Column(UUID(as_uuid=True), ForeignKey("meal_plans.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
