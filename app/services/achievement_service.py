"""
Achievement Detection Service.

Checks and awards milestones based on user activity.
Called after logging meals, workouts, weight, etc.
"""
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.achievement import Achievement
from app.models.daily_log import DailyLog, MealLog, WorkoutLog
from app.models.health_profile import HealthProfile


# Define all possible milestones
MILESTONES = [
    # Streak milestones
    {"type": "streak_3", "check": "streak", "value": 3, "title": "Getting Started", "desc": "Logged 3 days in a row!", "icon": "fire"},
    {"type": "streak_7", "check": "streak", "value": 7, "title": "One Week Warrior", "desc": "7-day logging streak!", "icon": "fire"},
    {"type": "streak_14", "check": "streak", "value": 14, "title": "Two Week Champion", "desc": "14-day logging streak!", "icon": "fire"},
    {"type": "streak_30", "check": "streak", "value": 30, "title": "Monthly Machine", "desc": "30-day logging streak!", "icon": "fire"},
    # Workout milestones
    {"type": "first_workout", "check": "workout_count", "value": 1, "title": "First Workout", "desc": "Completed your first workout!", "icon": "dumbbell"},
    {"type": "workouts_10", "check": "workout_count", "value": 10, "title": "10 Workouts Done", "desc": "Completed 10 workouts total!", "icon": "dumbbell"},
    {"type": "workouts_25", "check": "workout_count", "value": 25, "title": "25 Workouts Strong", "desc": "25 workouts completed — you're building a habit!", "icon": "arm-flex"},
    {"type": "workouts_50", "check": "workout_count", "value": 50, "title": "50 Workout Beast", "desc": "50 workouts! You're unstoppable!", "icon": "trophy"},
    {"type": "workouts_100", "check": "workout_count", "value": 100, "title": "Century Club", "desc": "100 workouts completed — legendary!", "icon": "trophy"},
    # Meal logging milestones
    {"type": "first_meal", "check": "meal_count", "value": 1, "title": "First Meal Logged", "desc": "Started tracking your nutrition!", "icon": "silverware-fork-knife"},
    {"type": "meals_50", "check": "meal_count", "value": 50, "title": "50 Meals Tracked", "desc": "50 meals logged — nutrition pro!", "icon": "silverware-fork-knife"},
    {"type": "meals_100", "check": "meal_count", "value": 100, "title": "100 Meals Tracked", "desc": "100 meals! Your data is gold!", "icon": "star"},
    # Weight milestones
    {"type": "weight_1kg", "check": "weight_loss", "value": 1, "title": "First Kilo Down", "desc": "Lost your first kilogram!", "icon": "scale-bathroom"},
    {"type": "weight_3kg", "check": "weight_loss", "value": 3, "title": "3kg Lighter", "desc": "Lost 3kg — visible progress!", "icon": "scale-bathroom"},
    {"type": "weight_5kg", "check": "weight_loss", "value": 5, "title": "5kg Transformation", "desc": "5kg lost — incredible work!", "icon": "star"},
    {"type": "weight_10kg", "check": "weight_loss", "value": 10, "title": "10kg Legend", "desc": "10kg lost — a new you!", "icon": "trophy"},
    # Active days
    {"type": "active_7", "check": "total_active", "value": 7, "title": "Week Warrior", "desc": "7 total active days!", "icon": "calendar-check"},
    {"type": "active_30", "check": "total_active", "value": 30, "title": "Monthly Active", "desc": "30 total active days!", "icon": "calendar-check"},
    {"type": "active_100", "check": "total_active", "value": 100, "title": "100 Day Journey", "desc": "100 days of tracking your health!", "icon": "medal"},
]


async def _has_achievement(db: AsyncSession, user_id: str, achievement_type: str) -> bool:
    result = await db.execute(
        select(Achievement).where(
            Achievement.user_id == user_id,
            Achievement.achievement_type == achievement_type,
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _get_current_streak(db: AsyncSession, user_id: str, today: date) -> int:
    meal_result = await db.execute(
        select(MealLog.log_date).where(MealLog.user_id == user_id).distinct()
    )
    workout_result = await db.execute(
        select(WorkoutLog.log_date).where(WorkoutLog.user_id == user_id).distinct()
    )
    active_dates = {r[0] for r in meal_result.all()} | {r[0] for r in workout_result.all()}

    streak = 0
    check = today
    while check in active_dates:
        streak += 1
        check -= timedelta(days=1)
    if streak == 0:
        check = today - timedelta(days=1)
        while check in active_dates:
            streak += 1
            check -= timedelta(days=1)
    return streak


async def check_and_award(db: AsyncSession, user_id: str) -> list[dict]:
    """Check all milestones and award any newly earned ones. Returns list of new achievements."""
    today = date.today()
    new_achievements = []

    # Precompute stats
    workout_count_result = await db.execute(
        select(func.count()).select_from(WorkoutLog).where(
            WorkoutLog.user_id == user_id, WorkoutLog.skipped == False
        )
    )
    workout_count = workout_count_result.scalar() or 0

    meal_count_result = await db.execute(
        select(func.count()).select_from(MealLog).where(MealLog.user_id == user_id)
    )
    meal_count = meal_count_result.scalar() or 0

    # Active days count
    meal_dates_result = await db.execute(
        select(MealLog.log_date).where(MealLog.user_id == user_id).distinct()
    )
    workout_dates_result = await db.execute(
        select(WorkoutLog.log_date).where(WorkoutLog.user_id == user_id).distinct()
    )
    total_active = len(
        {r[0] for r in meal_dates_result.all()} | {r[0] for r in workout_dates_result.all()}
    )

    # Streak
    current_streak = await _get_current_streak(db, user_id, today)

    # Weight loss (first weight ever vs current)
    weight_loss = 0
    profile_result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile and profile.weight_kg:
        first_weight = float(profile.weight_kg)
        latest_result = await db.execute(
            select(DailyLog.weight_kg).where(
                DailyLog.user_id == user_id,
                DailyLog.weight_kg.isnot(None),
            ).order_by(DailyLog.log_date.desc()).limit(1)
        )
        latest_row = latest_result.first()
        if latest_row and latest_row[0]:
            current_weight = float(latest_row[0])
            if profile.goal in ("weight_loss", "fat_loss"):
                weight_loss = first_weight - current_weight
            else:
                weight_loss = abs(current_weight - first_weight)

    # Check each milestone
    for m in MILESTONES:
        if await _has_achievement(db, user_id, m["type"]):
            continue

        earned = False
        if m["check"] == "streak" and current_streak >= m["value"]:
            earned = True
        elif m["check"] == "workout_count" and workout_count >= m["value"]:
            earned = True
        elif m["check"] == "meal_count" and meal_count >= m["value"]:
            earned = True
        elif m["check"] == "weight_loss" and weight_loss >= m["value"]:
            earned = True
        elif m["check"] == "total_active" and total_active >= m["value"]:
            earned = True

        if earned:
            achievement = Achievement(
                user_id=user_id,
                achievement_type=m["type"],
                title=m["title"],
                description=m["desc"],
                icon=m["icon"],
            )
            db.add(achievement)
            new_achievements.append({
                "type": m["type"],
                "title": m["title"],
                "description": m["desc"],
                "icon": m["icon"],
            })

    if new_achievements:
        await db.commit()

    return new_achievements


async def get_all_achievements(db: AsyncSession, user_id: str) -> dict:
    """Get all achievements for a user."""
    result = await db.execute(
        select(Achievement).where(Achievement.user_id == user_id)
            .order_by(Achievement.unlocked_at.desc())
    )
    unlocked = result.scalars().all()

    unlocked_types = {a.achievement_type for a in unlocked}

    return {
        "unlocked": [
            {
                "id": str(a.id),
                "type": a.achievement_type,
                "title": a.title,
                "description": a.description,
                "icon": a.icon,
                "unlocked_at": a.unlocked_at,
                "is_seen": a.is_seen,
            }
            for a in unlocked
        ],
        "locked": [
            {
                "type": m["type"],
                "title": m["title"],
                "description": m["desc"],
                "icon": m["icon"],
            }
            for m in MILESTONES if m["type"] not in unlocked_types
        ],
        "total_unlocked": len(unlocked),
        "total_milestones": len(MILESTONES),
    }


async def mark_seen(db: AsyncSession, user_id: str, achievement_ids: list[str]) -> dict:
    """Mark achievements as seen (dismiss celebration)."""
    result = await db.execute(
        select(Achievement).where(
            Achievement.user_id == user_id,
            Achievement.id.in_(achievement_ids),
        )
    )
    achievements = result.scalars().all()
    for a in achievements:
        a.is_seen = True
    await db.commit()
    return {"message": f"Marked {len(achievements)} achievements as seen"}
