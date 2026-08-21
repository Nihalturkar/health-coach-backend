from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.tracking import (
    LogMealRequest, LogWorkoutRequest, LogWaterRequest,
    LogWeightRequest, LogSleepRequest, MealLogResponse,
    WorkoutLogResponse, DailyLogResponse, TodaySummaryResponse, MessageResponse,
    UpdateMealRequest, UpdateWorkoutRequest, UpdateDailyLogRequest,
)
from app.services import tracking_service
from app.services.achievement_service import check_and_award

router = APIRouter(prefix="/track", tags=["Daily Tracking"])


@router.post("/meal", status_code=201)
async def log_meal(
    body: LogMealRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal = await tracking_service.log_meal(db, str(current_user.id), body.model_dump())
    new_achievements = await check_and_award(db, str(current_user.id))
    result = MealLogResponse.model_validate(meal).model_dump()
    result["new_achievements"] = new_achievements
    return result


@router.delete("/meal/{log_id}", response_model=MessageResponse)
async def delete_meal(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.delete_meal_log(db, str(current_user.id), log_id)


@router.put("/meal/{log_id}", response_model=MealLogResponse)
async def update_meal(
    log_id: str,
    body: UpdateMealRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.update_meal_log(
        db, str(current_user.id), log_id, body.model_dump(exclude_none=True)
    )


@router.post("/workout", status_code=201)
async def log_workout(
    body: LogWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await tracking_service.log_workout(db, str(current_user.id), body.model_dump())
    new_achievements = await check_and_award(db, str(current_user.id))
    result = WorkoutLogResponse.model_validate(workout).model_dump()
    result["new_achievements"] = new_achievements
    return result


@router.delete("/workout/{log_id}", response_model=MessageResponse)
async def delete_workout(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.delete_workout_log(db, str(current_user.id), log_id)


@router.put("/workout/{log_id}", response_model=WorkoutLogResponse)
async def update_workout(
    log_id: str,
    body: UpdateWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.update_workout_log(
        db, str(current_user.id), log_id, body.model_dump(exclude_none=True)
    )


@router.put("/daily", response_model=DailyLogResponse)
async def update_daily_log(
    body: UpdateDailyLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    log_date = data.pop("log_date")
    return await tracking_service.update_daily_log(
        db, str(current_user.id), log_date, data
    )


@router.post("/water", response_model=DailyLogResponse, status_code=201)
async def log_water(
    body: LogWaterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.log_water(db, str(current_user.id), body.log_date, body.water_ml)


@router.post("/weight", status_code=201)
async def log_weight(
    body: LogWeightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    daily = await tracking_service.log_weight(db, str(current_user.id), body.log_date, body.weight_kg)
    new_achievements = await check_and_award(db, str(current_user.id))
    result = DailyLogResponse.model_validate(daily).model_dump()
    result["new_achievements"] = new_achievements
    return result


@router.post("/sleep", response_model=DailyLogResponse, status_code=201)
async def log_sleep(
    body: LogSleepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.log_sleep(db, str(current_user.id), body.model_dump())


@router.get("/today", response_model=TodaySummaryResponse)
async def get_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.get_today_summary(db, str(current_user.id), date.today())


@router.get("/history")
async def get_history(
    start_date: date = Query(...),
    end_date: date = Query(...),
    page: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracking_service.get_history(
        db, str(current_user.id), start_date, end_date, page, limit
    )
