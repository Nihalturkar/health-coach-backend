from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.daily_log import DailyLog, MealLog, WorkoutLog
from app.models.progress import WeeklyReport
from app.models.health_profile import HealthProfile


def get_week_number(d: date) -> int:
    """Return ISO week number for a date."""
    return d.isocalendar()[1]


def get_week_bounds(week_number: int, year: int) -> tuple[date, date]:
    """Return start (Monday) and end (Sunday) of an ISO week."""
    jan4 = date(year, 1, 4)
    week_start = jan4 + timedelta(weeks=week_number - get_week_number(jan4), days=-jan4.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


async def get_dashboard(db: AsyncSession, user_id: str, today: date) -> dict:
    # Get health profile for targets
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    calories_target = profile.target_calories or 2000 if profile else 2000
    protein_target = profile.target_protein or 150 if profile else 150
    water_target = profile.target_water_ml or 3000 if profile else 3000

    # Today's daily log
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date == today
        )
    )
    daily = result.scalar_one_or_none()

    # Today's meal logs
    result = await db.execute(
        select(MealLog).where(
            MealLog.user_id == user_id,
            MealLog.log_date == today
        )
    )
    meals = result.scalars().all()

    calories_consumed = sum(m.calories or 0 for m in meals)
    protein_consumed = sum(float(m.protein_g or 0) for m in meals)
    water_ml = daily.water_ml if daily else 0
    weight_today = float(daily.weight_kg) if daily and daily.weight_kg else None
    sleep_hours = float(daily.sleep_hours) if daily and daily.sleep_hours else None
    mood = daily.mood if daily else None

    # This week's stats
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_number = get_week_number(today)

    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.log_date >= week_start,
            WorkoutLog.log_date <= today,
        )
    )
    week_workouts = result.scalars().all()
    workouts_completed = sum(1 for w in week_workouts if not w.skipped)
    workouts_planned = len(week_workouts)

    # Avg calories this week
    result = await db.execute(
        select(MealLog).where(
            MealLog.user_id == user_id,
            MealLog.log_date >= week_start,
            MealLog.log_date <= today,
        )
    )
    week_meals = result.scalars().all()

    days_in_week = max((today - week_start).days + 1, 1)
    week_total_cal = sum(m.calories or 0 for m in week_meals)
    week_total_prot = sum(float(m.protein_g or 0) for m in week_meals)
    avg_calories = round(week_total_cal / days_in_week)
    avg_protein = round(week_total_prot / days_in_week, 1)

    # Weight change this week
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= week_start,
            DailyLog.log_date <= today,
            DailyLog.weight_kg.isnot(None),
        ).order_by(DailyLog.log_date)
    )
    week_weights = result.scalars().all()

    weight_change = None
    if len(week_weights) >= 2:
        weight_change = round(
            float(week_weights[-1].weight_kg) - float(week_weights[0].weight_kg), 1
        )

    return {
        "today_date": today,
        "week_number": week_number,
        "calories_consumed": calories_consumed,
        "calories_target": calories_target,
        "protein_consumed": round(protein_consumed, 1),
        "protein_target": protein_target,
        "water_ml": water_ml,
        "water_target": water_target,
        "weight_today": weight_today,
        "sleep_hours": sleep_hours,
        "mood": mood,
        "workouts_completed_this_week": workouts_completed,
        "workouts_planned_this_week": workouts_planned,
        "avg_calories_this_week": avg_calories,
        "avg_protein_this_week": avg_protein,
        "weight_change_this_week": weight_change,
    }


async def get_graphs(db: AsyncSession, user_id: str, days: int = 30) -> dict:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= start_date,
            DailyLog.log_date <= end_date,
        ).order_by(DailyLog.log_date)
    )
    daily_logs = result.scalars().all()

    # Meal aggregates per day
    result = await db.execute(
        select(
            MealLog.log_date,
            func.sum(MealLog.calories).label("total_cal"),
            func.sum(MealLog.protein_g).label("total_prot"),
        ).where(
            MealLog.user_id == user_id,
            MealLog.log_date >= start_date,
            MealLog.log_date <= end_date,
        ).group_by(MealLog.log_date).order_by(MealLog.log_date)
    )
    meal_rows = result.all()

    meal_by_date = {row.log_date: row for row in meal_rows}

    weight_points = []
    water_points = []
    sleep_points = []

    for log in daily_logs:
        if log.weight_kg:
            weight_points.append({"date": log.log_date, "value": float(log.weight_kg)})
        if log.water_ml:
            water_points.append({"date": log.log_date, "value": float(log.water_ml)})
        if log.sleep_hours:
            sleep_points.append({"date": log.log_date, "value": float(log.sleep_hours)})

    cal_points = [
        {"date": row.log_date, "value": float(row.total_cal or 0)}
        for row in meal_rows
    ]
    prot_points = [
        {"date": row.log_date, "value": float(row.total_prot or 0)}
        for row in meal_rows
    ]

    return {
        "weight": weight_points,
        "calories": cal_points,
        "protein": prot_points,
        "water": water_points,
        "sleep": sleep_points,
    }


async def get_weekly_report(db: AsyncSession, user_id: str, week_number: int) -> WeeklyReport:
    result = await db.execute(
        select(WeeklyReport).where(
            WeeklyReport.user_id == user_id,
            WeeklyReport.week_number == week_number,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report found for week {week_number}. Weekly review runs every Sunday."
        )
    return report


async def generate_weekly_report_data(db: AsyncSession, user_id: str, week_number: int) -> dict:
    """Compute weekly stats from logs — used by weekly review workflow."""
    year = date.today().year
    week_start, week_end = get_week_bounds(week_number, year)

    # Weights
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= week_start,
            DailyLog.log_date <= week_end,
            DailyLog.weight_kg.isnot(None),
        ).order_by(DailyLog.log_date)
    )
    weight_logs = result.scalars().all()
    start_weight = float(weight_logs[0].weight_kg) if weight_logs else None
    end_weight = float(weight_logs[-1].weight_kg) if weight_logs else None

    # Meal aggregates
    result = await db.execute(
        select(
            func.avg(MealLog.calories).label("avg_cal"),
            func.avg(MealLog.protein_g).label("avg_prot"),
        ).where(
            MealLog.user_id == user_id,
            MealLog.log_date >= week_start,
            MealLog.log_date <= week_end,
        )
    )
    meal_agg = result.one()

    # Water
    result = await db.execute(
        select(func.avg(DailyLog.water_ml)).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= week_start,
            DailyLog.log_date <= week_end,
            DailyLog.water_ml.isnot(None),
        )
    )
    avg_water = result.scalar() or 0

    # Sleep
    result = await db.execute(
        select(func.avg(DailyLog.sleep_hours)).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= week_start,
            DailyLog.log_date <= week_end,
            DailyLog.sleep_hours.isnot(None),
        )
    )
    avg_sleep = result.scalar() or 0

    # Workouts
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.log_date >= week_start,
            WorkoutLog.log_date <= week_end,
        )
    )
    workouts = result.scalars().all()
    completed = sum(1 for w in workouts if not w.skipped)
    skipped = sum(1 for w in workouts if w.skipped)

    return {
        "week_number": week_number,
        "start_date": week_start,
        "end_date": week_end,
        "start_weight": start_weight,
        "end_weight": end_weight,
        "avg_calories_consumed": round(meal_agg.avg_cal) if meal_agg.avg_cal else None,
        "avg_protein_consumed": round(float(meal_agg.avg_prot)) if meal_agg.avg_prot else None,
        "avg_water_ml": round(avg_water),
        "avg_sleep_hours": round(float(avg_sleep), 1),
        "workouts_completed": completed,
        "workouts_skipped": skipped,
    }
