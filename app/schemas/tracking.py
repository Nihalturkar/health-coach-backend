from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime


class LogMealRequest(BaseModel):
    log_date: date
    meal_type: str
    meal_name: str
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fats_g: Optional[float] = None
    is_from_plan: bool = False
    meal_plan_id: Optional[UUID] = None

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, v):
        valid = ["breakfast", "mid_morning", "lunch", "evening_snack", "dinner", "post_workout", "shake"]
        if v not in valid:
            raise ValueError(f"meal_type must be one of {valid}")
        return v


class LogWorkoutRequest(BaseModel):
    log_date: date
    workout_plan_id: Optional[UUID] = None
    duration_min: Optional[int] = None
    calories_burned: Optional[int] = None
    completed_exercises: Optional[int] = None
    total_exercises: Optional[int] = None
    feeling: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

    @field_validator("feeling")
    @classmethod
    def validate_feeling(cls, v):
        if v and v not in ["easy", "moderate", "hard", "exhausting"]:
            raise ValueError("feeling must be easy, moderate, hard, or exhausting")
        return v


class LogWaterRequest(BaseModel):
    log_date: date
    water_ml: int

    @field_validator("water_ml")
    @classmethod
    def validate_water(cls, v):
        if v <= 0:
            raise ValueError("water_ml must be positive")
        return v


class LogWeightRequest(BaseModel):
    log_date: date
    weight_kg: float

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v):
        if not (20 <= v <= 300):
            raise ValueError("weight_kg must be between 20 and 300")
        return v


class LogSleepRequest(BaseModel):
    log_date: date
    sleep_hours: float
    energy_level: Optional[int] = None
    mood: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("sleep_hours")
    @classmethod
    def validate_sleep(cls, v):
        if not (0 <= v <= 24):
            raise ValueError("sleep_hours must be between 0 and 24")
        return v

    @field_validator("energy_level")
    @classmethod
    def validate_energy(cls, v):
        if v and not (1 <= v <= 5):
            raise ValueError("energy_level must be between 1 and 5")
        return v

    @field_validator("mood")
    @classmethod
    def validate_mood(cls, v):
        if v and v not in ["great", "good", "okay", "low", "bad"]:
            raise ValueError("mood must be great, good, okay, low, or bad")
        return v


class MealLogResponse(BaseModel):
    id: UUID
    log_date: date
    meal_type: str
    meal_name: str
    calories: Optional[int]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fats_g: Optional[float]
    is_from_plan: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutLogResponse(BaseModel):
    id: UUID
    log_date: date
    workout_plan_id: Optional[UUID]
    duration_min: Optional[int]
    calories_burned: Optional[int]
    completed_exercises: Optional[int]
    total_exercises: Optional[int]
    feeling: Optional[str]
    skipped: bool
    skip_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DailyLogResponse(BaseModel):
    id: Optional[UUID]
    log_date: date
    weight_kg: Optional[float]
    water_ml: Optional[int]
    sleep_hours: Optional[float]
    energy_level: Optional[int]
    mood: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class TodaySummaryResponse(BaseModel):
    date: date
    daily_log: Optional[DailyLogResponse]
    meal_logs: List[MealLogResponse]
    workout_logs: List[WorkoutLogResponse]
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fats: float
    total_water_ml: int


class MessageResponse(BaseModel):
    message: str
