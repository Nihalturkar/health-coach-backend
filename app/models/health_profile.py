import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base

class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    height_cm = Column(Numeric(5, 2), nullable=False)
    weight_kg = Column(Numeric(5, 2), nullable=False)
    target_weight_kg = Column(Numeric(5, 2), nullable=True)
    activity_level = Column(String(20), nullable=False)
    goal = Column(String(20), nullable=False)
    food_preference = Column(String(20), default="non_veg")
    budget_level = Column(String(10), default="medium")
    workout_location = Column(String(10), default="home")
    fitness_level = Column(String(15), default="beginner")
    available_equipment = Column(ARRAY(String), nullable=True)
    medical_conditions = Column(ARRAY(String), nullable=True)
    allergies = Column(ARRAY(String), nullable=True)
    bmi = Column(Numeric(4, 1), nullable=True)
    bmr = Column(Numeric(7, 1), nullable=True)
    tdee = Column(Numeric(7, 1), nullable=True)
    target_calories = Column(Integer, nullable=True)
    target_protein = Column(Integer, nullable=True)
    target_carbs = Column(Integer, nullable=True)
    target_fats = Column(Integer, nullable=True)
    target_water_ml = Column(Integer, nullable=True)
    ideal_weight_kg = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
