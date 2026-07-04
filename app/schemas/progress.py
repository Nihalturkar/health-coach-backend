from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import date, datetime


class DashboardResponse(BaseModel):
    today_date: date
    week_number: int

    # Today stats
    calories_consumed: int
    calories_target: int
    protein_consumed: float
    protein_target: int
    water_ml: int
    water_target: int
    weight_today: Optional[float]
    sleep_hours: Optional[float]
    mood: Optional[str]

    # Week stats
    workouts_completed_this_week: int
    workouts_planned_this_week: int
    avg_calories_this_week: int
    avg_protein_this_week: float
    weight_change_this_week: Optional[float]


class GraphPoint(BaseModel):
    date: date
    value: float


class GraphsResponse(BaseModel):
    weight: List[GraphPoint]
    calories: List[GraphPoint]
    protein: List[GraphPoint]
    water: List[GraphPoint]
    sleep: List[GraphPoint]


class WeeklyReportResponse(BaseModel):
    id: UUID
    week_number: int
    start_date: date
    end_date: date
    start_weight: Optional[float]
    end_weight: Optional[float]
    avg_calories_consumed: Optional[int]
    avg_protein_consumed: Optional[int]
    avg_water_ml: Optional[int]
    workouts_completed: Optional[int]
    workouts_skipped: Optional[int]
    avg_sleep_hours: Optional[float]
    ai_summary: Optional[str]
    ai_suggestions: Optional[Any]
    plan_adjustments: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True
