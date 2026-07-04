"""
Diet Plan Workflow — with validation + cache + retry.

Flow: Cache Check → Generate Plan (LLM) → Validate Nutrition → Adjust if needed → Save → Cache
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.ai.agent import call_groq_json
from app.ai.prompts.diet_prompt import get_diet_prompt, get_alternative_prompt
from app.ai.mcp_servers.nutrition_mcp import validate_day_nutrition, adjust_portions, validate_meal_coverage
from app.redis import cache_get, cache_set
from app.models.meal_plan import MealPlan
from app.models.health_profile import HealthProfile


async def generate_diet_plan(db: AsyncSession, user_id: str, week_number: int) -> list:
    """Full diet plan workflow: cache → LLM → validate → retry → save."""

    # --- Node 1: Cache Check ---
    cache_key = f"meal_plan:{user_id}:{week_number}"
    cached = await cache_get(cache_key)
    if cached:
        result = await db.execute(
            select(MealPlan).where(
                MealPlan.user_id == user_id,
                MealPlan.week_number == week_number,
                MealPlan.is_active == True,
            ).limit(1)
        )
        if result.scalar_one_or_none():
            return []  # already in DB, skip generation

    # --- Node 2: Get Profile ---
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise ValueError("Health profile not found. Complete onboarding first.")

    profile_data = {
        "age": profile.age,
        "gender": profile.gender,
        "weight_kg": float(profile.weight_kg),
        "height_cm": float(profile.height_cm),
        "goal": profile.goal,
        "activity_level": profile.activity_level,
        "food_preference": profile.food_preference,
        "budget_level": profile.budget_level,
        "medical_conditions": profile.medical_conditions or [],
        "allergies": profile.allergies or [],
        "target_calories": profile.target_calories,
        "target_protein": profile.target_protein,
        "target_carbs": profile.target_carbs,
        "target_fats": profile.target_fats,
    }

    # --- Node 3: Generate Plan (Groq LLM) ---
    prompt = get_diet_prompt(profile_data)
    plan_data = call_groq_json(
        system_prompt="You are a professional nutritionist. Return only valid JSON.",
        user_prompt=prompt,
    )

    # --- Node 4: Validate Nutrition (MCP Tools) ---
    days = plan_data.get("days", [])
    for day in days:
        meals = day.get("meals", [])

        # Check meal coverage
        coverage = validate_meal_coverage(meals)

        # Check nutrition targets
        nutrition = validate_day_nutrition(
            meals, profile.target_calories or 2000, profile.target_protein or 150
        )

        # If nutrition check fails, adjust portions programmatically
        if not nutrition["passed"]:
            day["meals"] = adjust_portions(meals, profile.target_calories or 2000)

    # --- Node 5: Delete old + Save to DB ---
    await db.execute(
        delete(MealPlan).where(
            MealPlan.user_id == user_id,
            MealPlan.week_number == week_number,
        )
    )

    saved_meals = []
    for day in days:
        day_of_week = day.get("day_of_week", 1)
        for meal in day.get("meals", []):
            meal_plan = MealPlan(
                user_id=user_id,
                week_number=week_number,
                day_of_week=day_of_week,
                meal_type=meal.get("meal_type", "breakfast"),
                meal_name=meal.get("meal_name", "Unnamed Meal"),
                description=meal.get("description"),
                recipe=meal.get("recipe"),
                ingredients=meal.get("ingredients"),
                calories=meal.get("calories", 0),
                protein_g=meal.get("protein_g"),
                carbs_g=meal.get("carbs_g"),
                fats_g=meal.get("fats_g"),
                fiber_g=meal.get("fiber_g"),
                prep_time_min=meal.get("prep_time_min"),
                is_alternative=False,
                is_active=True,
            )
            db.add(meal_plan)
            saved_meals.append(meal_plan)

    await db.commit()
    for meal in saved_meals:
        await db.refresh(meal)

    # --- Node 6: Write-through Cache ---
    cache_data = {"week": week_number, "total_meals": len(saved_meals)}
    await cache_set(cache_key, cache_data, ttl_seconds=7 * 24 * 3600)

    return saved_meals


async def generate_alternatives(db: AsyncSession, user_id: str, meal_id: str) -> list:
    """Generate 2 alternative meals for a given meal via Groq LLM."""

    result = await db.execute(
        select(MealPlan).where(MealPlan.id == meal_id, MealPlan.user_id == user_id)
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise ValueError("Meal not found")

    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    meal_data = {
        "meal_name": meal.meal_name,
        "meal_type": meal.meal_type,
        "calories": meal.calories,
        "protein_g": float(meal.protein_g) if meal.protein_g else 0,
    }
    profile_data = {
        "food_preference": profile.food_preference if profile else "non_veg",
        "allergies": profile.allergies if profile else [],
    }

    prompt = get_alternative_prompt(meal_data, profile_data)
    alt_data = call_groq_json(
        system_prompt="You are a nutritionist. Return only valid JSON.",
        user_prompt=prompt,
    )

    saved_alts = []
    for alt in alt_data.get("alternatives", []):
        alt_meal = MealPlan(
            user_id=user_id,
            week_number=meal.week_number,
            day_of_week=meal.day_of_week,
            meal_type=meal.meal_type,
            meal_name=alt.get("meal_name", "Alternative"),
            description=alt.get("description"),
            recipe=alt.get("recipe"),
            ingredients=alt.get("ingredients"),
            calories=alt.get("calories", meal.calories),
            protein_g=alt.get("protein_g"),
            carbs_g=alt.get("carbs_g"),
            fats_g=alt.get("fats_g"),
            fiber_g=alt.get("fiber_g"),
            prep_time_min=alt.get("prep_time_min"),
            is_alternative=True,
            alternative_for=meal.id,
            is_active=True,
        )
        db.add(alt_meal)
        saved_alts.append(alt_meal)

    await db.commit()
    for alt in saved_alts:
        await db.refresh(alt)

    return saved_alts
