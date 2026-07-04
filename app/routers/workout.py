from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.workout_plan import WorkoutPlan, WorkoutExercise
from app.schemas.ai import GeneratePlanRequest
from app.ai.workflows.workout_planner import generate_workout_plan

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
