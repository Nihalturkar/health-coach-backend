from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status

from app.models.daily_log import DailyLog, MealLog, WorkoutLog


async def log_meal(db: AsyncSession, user_id: str, data: dict) -> MealLog:
    meal = MealLog(user_id=user_id, **data)
    db.add(meal)
    await db.commit()
    await db.refresh(meal)
    return meal


async def delete_meal_log(db: AsyncSession, user_id: str, log_id: str) -> dict:
    result = await db.execute(
        select(MealLog).where(MealLog.id == log_id, MealLog.user_id == user_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal log not found")
    await db.delete(log)
    await db.commit()
    return {"message": "Meal log deleted"}


async def log_workout(db: AsyncSession, user_id: str, data: dict) -> WorkoutLog:
    workout = WorkoutLog(user_id=user_id, **data)
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


async def delete_workout_log(db: AsyncSession, user_id: str, log_id: str) -> dict:
    result = await db.execute(
        select(WorkoutLog).where(WorkoutLog.id == log_id, WorkoutLog.user_id == user_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found")
    await db.delete(log)
    await db.commit()
    return {"message": "Workout log deleted"}


async def log_water(db: AsyncSession, user_id: str, log_date: date, water_ml: int) -> DailyLog:
    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == log_date)
    )
    daily = result.scalar_one_or_none()
    if daily:
        daily.water_ml = (daily.water_ml or 0) + water_ml
    else:
        daily = DailyLog(user_id=user_id, log_date=log_date, water_ml=water_ml)
        db.add(daily)
    await db.commit()
    await db.refresh(daily)
    return daily


async def log_weight(db: AsyncSession, user_id: str, log_date: date, weight_kg: float) -> DailyLog:
    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == log_date)
    )
    daily = result.scalar_one_or_none()
    if daily:
        daily.weight_kg = weight_kg
    else:
        daily = DailyLog(user_id=user_id, log_date=log_date, weight_kg=weight_kg)
        db.add(daily)
    await db.commit()
    await db.refresh(daily)
    return daily


async def log_sleep(db: AsyncSession, user_id: str, data: dict) -> DailyLog:
    log_date = data.pop("log_date")
    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == log_date)
    )
    daily = result.scalar_one_or_none()
    if daily:
        for key, value in data.items():
            if value is not None:
                setattr(daily, key, value)
    else:
        daily = DailyLog(user_id=user_id, log_date=log_date, **data)
        db.add(daily)
    await db.commit()
    await db.refresh(daily)
    return daily


async def get_today_summary(db: AsyncSession, user_id: str, today: date) -> dict:
    # Daily log
    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == today)
    )
    daily = result.scalar_one_or_none()

    # Meal logs
    result = await db.execute(
        select(MealLog).where(MealLog.user_id == user_id, MealLog.log_date == today)
    )
    meals = result.scalars().all()

    # Workout logs
    result = await db.execute(
        select(WorkoutLog).where(WorkoutLog.user_id == user_id, WorkoutLog.log_date == today)
    )
    workouts = result.scalars().all()

    total_calories = sum(m.calories or 0 for m in meals)
    total_protein = sum(float(m.protein_g or 0) for m in meals)
    total_carbs = sum(float(m.carbs_g or 0) for m in meals)
    total_fats = sum(float(m.fats_g or 0) for m in meals)
    total_water = daily.water_ml if daily else 0

    return {
        "date": today,
        "daily_log": daily,
        "meal_logs": list(meals),
        "workout_logs": list(workouts),
        "total_calories": total_calories,
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fats": round(total_fats, 1),
        "total_water_ml": total_water,
    }


async def get_history(
    db: AsyncSession, user_id: str, start_date: date, end_date: date, page: int, limit: int
) -> dict:
    offset = (page - 1) * limit

    result = await db.execute(
        select(DailyLog)
        .where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= start_date,
            DailyLog.log_date <= end_date,
        )
        .order_by(DailyLog.log_date.desc())
        .offset(offset)
        .limit(limit)
    )
    daily_logs = result.scalars().all()

    result = await db.execute(
        select(MealLog)
        .where(
            MealLog.user_id == user_id,
            MealLog.log_date >= start_date,
            MealLog.log_date <= end_date,
        )
        .order_by(MealLog.log_date.desc())
    )
    meal_logs = result.scalars().all()

    result = await db.execute(
        select(WorkoutLog)
        .where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.log_date >= start_date,
            WorkoutLog.log_date <= end_date,
        )
        .order_by(WorkoutLog.log_date.desc())
    )
    workout_logs = result.scalars().all()

    return {
        "daily_logs": list(daily_logs),
        "meal_logs": list(meal_logs),
        "workout_logs": list(workout_logs),
        "page": page,
        "limit": limit,
    }
