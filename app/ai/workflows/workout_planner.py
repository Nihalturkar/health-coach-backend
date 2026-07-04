"""
Workout Plan Workflow — with split determination + validation.

Flow: Determine Split (MCP) → Generate Exercises (LLM) → Validate (MCP) → Save
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.ai.agent import call_groq_json
from app.ai.prompts.workout_prompt import get_workout_prompt
from app.ai.mcp_servers.workout_mcp import determine_split, validate_workout_day, validate_consecutive_muscles
from app.models.workout_plan import WorkoutPlan, WorkoutExercise
from app.models.health_profile import HealthProfile


async def generate_workout_plan(db: AsyncSession, user_id: str, week_number: int) -> list:
    """Full workout plan workflow: split → LLM → validate → save."""

    # --- Node 1: Get Profile ---
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise ValueError("Health profile not found")

    # --- Node 2: Determine Split (MCP Tool) ---
    fitness_level = profile.fitness_level or "beginner"
    split = determine_split(fitness_level)

    profile_data = {
        "age": profile.age,
        "gender": profile.gender,
        "weight_kg": float(profile.weight_kg),
        "height_cm": float(profile.height_cm),
        "goal": profile.goal,
        "fitness_level": fitness_level,
        "workout_location": profile.workout_location or "home",
        "available_equipment": profile.available_equipment or [],
        "medical_conditions": profile.medical_conditions or [],
    }

    # --- Node 3: Generate Exercises (Groq LLM) ---
    prompt = get_workout_prompt(profile_data)
    plan_data = call_groq_json(
        system_prompt="You are a certified fitness trainer. Return only valid JSON.",
        user_prompt=prompt,
    )

    # --- Node 4: Validate (MCP Tools) ---
    days = plan_data.get("days", [])

    # Check consecutive muscle groups
    validate_consecutive_muscles(days)

    # Individual day validation — remove exercises with unavailable equipment
    for day in days:
        if day.get("workout_type") == "rest":
            continue
        day_check = validate_workout_day(
            day.get("exercises", []),
            profile_data["available_equipment"],
            day.get("workout_type", "full_body"),
        )
        if not day_check["passed"]:
            day["exercises"] = [
                ex for ex in day.get("exercises", [])
                if ex.get("equipment", "bodyweight") == "bodyweight"
                or ex.get("equipment") in profile_data["available_equipment"]
            ]

    # --- Node 5: Delete old + Save ---
    await db.execute(
        delete(WorkoutPlan).where(
            WorkoutPlan.user_id == user_id,
            WorkoutPlan.week_number == week_number,
        )
    )

    saved_plans = []
    for day in days:
        workout = WorkoutPlan(
            user_id=user_id,
            week_number=week_number,
            day_of_week=day.get("day_of_week", 1),
            workout_type=day.get("workout_type", "full_body"),
            title=day.get("title", "Workout"),
            duration_min=day.get("duration_min"),
            location=day.get("location", profile_data["workout_location"]),
            is_active=True,
        )
        db.add(workout)
        await db.flush()

        for ex in day.get("exercises", []):
            exercise = WorkoutExercise(
                workout_plan_id=workout.id,
                exercise_name=ex.get("exercise_name", "Unknown"),
                sets=ex.get("sets"),
                reps=ex.get("reps"),
                rest_seconds=ex.get("rest_seconds"),
                suggested_weight_kg=ex.get("suggested_weight_kg"),
                instructions=ex.get("instructions"),
                muscle_group=ex.get("muscle_group"),
                equipment=ex.get("equipment", "bodyweight"),
                order_index=ex.get("order_index", 1),
            )
            db.add(exercise)

        saved_plans.append(workout)

    await db.commit()
    for plan in saved_plans:
        await db.refresh(plan)

    return saved_plans
