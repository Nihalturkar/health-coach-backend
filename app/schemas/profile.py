from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


class Goal(str, Enum):
    weight_loss = "weight_loss"
    weight_gain = "weight_gain"
    muscle_gain = "muscle_gain"
    maintain = "maintain"
    general_fitness = "general_fitness"


class FoodPreference(str, Enum):
    veg = "veg"
    non_veg = "non_veg"
    vegan = "vegan"
    eggetarian = "eggetarian"


class BudgetLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class WorkoutLocation(str, Enum):
    home = "home"
    gym = "gym"
    both = "both"


class FitnessLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class OnboardingRequest(BaseModel):
    age: int
    gender: Gender
    height_cm: float
    weight_kg: float
    target_weight_kg: Optional[float] = None
    activity_level: ActivityLevel
    goal: Goal
    food_preference: FoodPreference = FoodPreference.non_veg
    budget_level: BudgetLevel = BudgetLevel.medium
    workout_location: WorkoutLocation = WorkoutLocation.home
    fitness_level: FitnessLevel = FitnessLevel.beginner
    available_equipment: Optional[List[str]] = []
    medical_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if not (10 <= v <= 100):
            raise ValueError("Age must be between 10 and 100")
        return v

    @field_validator("height_cm")
    @classmethod
    def validate_height(cls, v):
        if not (100 <= v <= 250):
            raise ValueError("Height must be between 100 and 250 cm")
        return v

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v):
        if not (20 <= v <= 300):
            raise ValueError("Weight must be between 20 and 300 kg")
        return v


class UpdateProfileRequest(BaseModel):
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None
    food_preference: Optional[FoodPreference] = None
    budget_level: Optional[BudgetLevel] = None
    workout_location: Optional[WorkoutLocation] = None
    fitness_level: Optional[FitnessLevel] = None
    available_equipment: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None


class AssessmentResult(BaseModel):
    bmi: float
    bmi_category: str
    bmr: float
    tdee: float
    target_calories: int
    target_protein: int
    target_carbs: int
    target_fats: int
    target_water_ml: int
    ideal_weight_kg: float
    summary: str


class HealthProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    target_weight_kg: Optional[float]
    activity_level: str
    goal: str
    food_preference: str
    budget_level: str
    workout_location: str
    fitness_level: str
    available_equipment: Optional[List[str]]
    medical_conditions: Optional[List[str]]
    allergies: Optional[List[str]]
    bmi: Optional[float]
    bmr: Optional[float]
    tdee: Optional[float]
    target_calories: Optional[int]
    target_protein: Optional[int]
    target_carbs: Optional[int]
    target_fats: Optional[int]
    target_water_ml: Optional[int]
    ideal_weight_kg: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
