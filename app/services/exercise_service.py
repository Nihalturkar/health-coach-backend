"""
Exercise Performance Tracking Service.
Logs per-set data and provides history for progressive overload tracking.
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.exercise_log import ExerciseLog


async def log_exercise(db: AsyncSession, user_id: str, data: dict) -> ExerciseLog:
    """Log performance for a single exercise with per-set data."""
    sets_data = data.get("sets_data", [])
    total_sets = len(sets_data)
    total_reps = sum(s.get("reps", 0) for s in sets_data)
    max_weight = max((s.get("weight_kg", 0) for s in sets_data), default=0)
    total_volume = sum(
        s.get("reps", 0) * s.get("weight_kg", 0) for s in sets_data
    )

    log = ExerciseLog(
        user_id=user_id,
        log_date=data.get("log_date", date.today()),
        exercise_name=data["exercise_name"],
        muscle_group=data.get("muscle_group"),
        sets_data=sets_data,
        total_sets=total_sets,
        total_reps=total_reps,
        max_weight_kg=max_weight if max_weight > 0 else None,
        total_volume_kg=total_volume if total_volume > 0 else None,
        notes=data.get("notes"),
        workout_plan_id=data.get("workout_plan_id"),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_exercise_history(
    db: AsyncSession, user_id: str, exercise_name: str, limit: int = 20
) -> list[dict]:
    """Get performance history for a specific exercise (for progressive overload charts)."""
    result = await db.execute(
        select(ExerciseLog).where(
            ExerciseLog.user_id == user_id,
            ExerciseLog.exercise_name == exercise_name,
        ).order_by(ExerciseLog.log_date.desc()).limit(limit)
    )
    logs = result.scalars().all()

    return [
        {
            "id": str(log.id),
            "log_date": log.log_date,
            "sets_data": log.sets_data,
            "total_sets": log.total_sets,
            "total_reps": log.total_reps,
            "max_weight_kg": float(log.max_weight_kg) if log.max_weight_kg else None,
            "total_volume_kg": float(log.total_volume_kg) if log.total_volume_kg else None,
            "notes": log.notes,
        }
        for log in logs
    ]


async def get_personal_records(db: AsyncSession, user_id: str) -> list[dict]:
    """Get personal records (max weight) for each exercise the user has logged."""
    result = await db.execute(
        select(
            ExerciseLog.exercise_name,
            func.max(ExerciseLog.max_weight_kg).label("pr_weight"),
            func.max(ExerciseLog.total_volume_kg).label("pr_volume"),
            func.count().label("sessions"),
        ).where(ExerciseLog.user_id == user_id)
        .group_by(ExerciseLog.exercise_name)
        .order_by(func.max(ExerciseLog.max_weight_kg).desc())
    )
    rows = result.all()

    return [
        {
            "exercise_name": row.exercise_name,
            "pr_weight_kg": float(row.pr_weight) if row.pr_weight else None,
            "pr_volume_kg": float(row.pr_volume) if row.pr_volume else None,
            "sessions": row.sessions,
        }
        for row in rows
    ]


async def get_last_performance(
    db: AsyncSession, user_id: str, exercise_name: str
) -> dict | None:
    """Get the most recent performance for an exercise (used to suggest weights)."""
    result = await db.execute(
        select(ExerciseLog).where(
            ExerciseLog.user_id == user_id,
            ExerciseLog.exercise_name == exercise_name,
        ).order_by(ExerciseLog.log_date.desc()).limit(1)
    )
    log = result.scalar_one_or_none()
    if not log:
        return None

    return {
        "log_date": log.log_date,
        "sets_data": log.sets_data,
        "max_weight_kg": float(log.max_weight_kg) if log.max_weight_kg else None,
        "total_volume_kg": float(log.total_volume_kg) if log.total_volume_kg else None,
    }
