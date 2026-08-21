from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.workout_plan import WorkoutPlan, WorkoutExercise
from app.models.feedback import ExerciseFeedback
from app.schemas.ai import GeneratePlanRequest
from app.ai.workflows.workout_planner import generate_workout_plan
from app.services import exercise_service

router = APIRouter(prefix="/workout", tags=["Workout Plans"])


async def _format_workout_day(db: AsyncSession, workout: WorkoutPlan) -> dict:
    result = await db.execute(
        select(WorkoutExercise).where(
            WorkoutExercise.workout_plan_id == workout.id
        ).order_by(WorkoutExercise.order_index)
    )
    exercises = result.scalars().all()

    return {
        "id": str(workout.id),
        "day_of_week": workout.day_of_week,
        "workout_type": workout.workout_type,
        "title": workout.title,
        "duration_min": workout.duration_min,
        "location": workout.location,
        "exercises": [
            {
                "id": str(ex.id),
                "exercise_name": ex.exercise_name,
                "sets": ex.sets,
                "reps": ex.reps,
                "rest_seconds": ex.rest_seconds,
                "suggested_weight_kg": float(ex.suggested_weight_kg) if ex.suggested_weight_kg else None,
                "instructions": ex.instructions,
                "muscle_group": ex.muscle_group,
                "equipment": ex.equipment,
                "gif_url": ex.gif_url,
            }
            for ex in exercises
        ],
    }


@router.get("/current")
async def get_current_workout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    week_number = date.today().isocalendar()[1]
    result = await db.execute(
        select(WorkoutPlan).where(
            WorkoutPlan.user_id == str(current_user.id),
            WorkoutPlan.week_number == week_number,
            WorkoutPlan.is_active == True,
        ).order_by(WorkoutPlan.day_of_week)
    )
    workouts = result.scalars().all()
    if not workouts:
        raise HTTPException(status_code=404, detail="No workout plan for this week. Generate one first.")

    days = []
    for w in workouts:
        days.append(await _format_workout_day(db, w))

    return {"week_number": week_number, "days": days}


@router.get("/week/{week_number}")
async def get_workout_week(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkoutPlan).where(
            WorkoutPlan.user_id == str(current_user.id),
            WorkoutPlan.week_number == week_number,
            WorkoutPlan.is_active == True,
        ).order_by(WorkoutPlan.day_of_week)
    )
    workouts = result.scalars().all()
    if not workouts:
        raise HTTPException(status_code=404, detail=f"No workout plan for week {week_number}.")

    days = []
    for w in workouts:
        days.append(await _format_workout_day(db, w))

    return {"week_number": week_number, "days": days}


@router.post("/generate")
async def generate_workout(
    body: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    week_number = body.week_number or date.today().isocalendar()[1]
    plans = await generate_workout_plan(db, str(current_user.id), week_number)
    return {"message": f"Workout plan generated for week {week_number}", "total_days": len(plans)}


@router.put("/swap/{exercise_id}")
async def swap_exercise(
    exercise_id: str,
    new_exercise_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkoutExercise).where(WorkoutExercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Verify ownership
    result = await db.execute(
        select(WorkoutPlan).where(
            WorkoutPlan.id == exercise.workout_plan_id,
            WorkoutPlan.user_id == str(current_user.id),
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not your workout plan")

    exercise.exercise_name = new_exercise_name
    await db.commit()
    await db.refresh(exercise)
    return {"message": f"Exercise swapped to {new_exercise_name}"}


@router.get("/exercise/{exercise_id}")
async def get_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkoutExercise).where(WorkoutExercise.id == exercise_id)
    )
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return {
        "id": str(ex.id),
        "exercise_name": ex.exercise_name,
        "sets": ex.sets,
        "reps": ex.reps,
        "rest_seconds": ex.rest_seconds,
        "suggested_weight_kg": float(ex.suggested_weight_kg) if ex.suggested_weight_kg else None,
        "instructions": ex.instructions,
        "muscle_group": ex.muscle_group,
        "equipment": ex.equipment,
        "gif_url": ex.gif_url,
        "video_url": ex.video_url,
    }


# --- Exercise Performance Logging ---

class SetData(BaseModel):
    set_number: int
    reps: int
    weight_kg: float = 0


class LogExerciseRequest(BaseModel):
    log_date: Optional[str] = None
    exercise_name: str
    muscle_group: Optional[str] = None
    sets_data: list[SetData]
    notes: Optional[str] = None
    workout_plan_id: Optional[str] = None


@router.post("/exercise-log")
async def log_exercise_performance(
    body: LogExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump()
    data["sets_data"] = [s.model_dump() for s in body.sets_data]
    log = await exercise_service.log_exercise(db, str(current_user.id), data)
    return {
        "id": str(log.id),
        "exercise_name": log.exercise_name,
        "total_sets": log.total_sets,
        "total_reps": log.total_reps,
        "max_weight_kg": float(log.max_weight_kg) if log.max_weight_kg else None,
        "total_volume_kg": float(log.total_volume_kg) if log.total_volume_kg else None,
    }


@router.get("/exercise-history/{exercise_name}")
async def get_exercise_history(
    exercise_name: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await exercise_service.get_exercise_history(
        db, str(current_user.id), exercise_name, limit
    )


@router.get("/personal-records")
async def get_personal_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await exercise_service.get_personal_records(db, str(current_user.id))


@router.get("/last-performance/{exercise_name}")
async def get_last_performance(
    exercise_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await exercise_service.get_last_performance(
        db, str(current_user.id), exercise_name
    )
    return result or {"message": "No previous performance found"}


# --- Exercise Feedback ---

class ExerciseFeedbackRequest(BaseModel):
    exercise_name: str
    difficulty: str  # "too_easy", "just_right", "too_hard", "painful"
    notes: Optional[str] = None


@router.post("/feedback")
async def submit_exercise_feedback(
    body: ExerciseFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback = ExerciseFeedback(
        user_id=str(current_user.id),
        exercise_name=body.exercise_name,
        difficulty=body.difficulty,
        notes=body.notes,
    )
    db.add(feedback)
    await db.commit()
    return {"message": "Feedback saved"}


@router.get("/feedback/summary")
async def get_exercise_feedback_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExerciseFeedback).where(
            ExerciseFeedback.user_id == str(current_user.id),
        ).order_by(ExerciseFeedback.created_at.desc()).limit(50)
    )
    feedbacks = result.scalars().all()

    too_hard = [f.exercise_name for f in feedbacks if f.difficulty in ("too_hard", "painful")]
    too_easy = [f.exercise_name for f in feedbacks if f.difficulty == "too_easy"]

    return {
        "too_hard_exercises": too_hard[:10],
        "too_easy_exercises": too_easy[:10],
        "total_feedback": len(feedbacks),
    }
