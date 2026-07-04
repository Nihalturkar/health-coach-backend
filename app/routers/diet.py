from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.meal_plan import MealPlan
from app.schemas.ai import GeneratePlanRequest
from app.ai.workflows.diet_planner import generate_diet_plan, generate_alternatives

router = APIRouter(prefix="/diet", tags=["Diet Plans"])


@router.get("/current")
async def get_current_diet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    week_number = date.today().isocalendar()[1]
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.user_id == str(current_user.id),
            MealPlan.week_number == week_number,
            MealPlan.is_alternative == False,
            MealPlan.is_active == True,
        ).order_by(MealPlan.day_of_week, MealPlan.meal_type)
    )
    meals = result.scalars().all()
    if not meals:
        raise HTTPException(status_code=404, detail="No diet plan for this week. Generate one first.")

    days = {}
    for meal in meals:
        day = meal.day_of_week
        if day not in days:
            days[day] = []
        days[day].append({
            "id": str(meal.id),
            "meal_type": meal.meal_type,
            "meal_name": meal.meal_name,
            "description": meal.description,
            "calories": meal.calories,
            "protein_g": float(meal.protein_g) if meal.protein_g else None,
            "carbs_g": float(meal.carbs_g) if meal.carbs_g else None,
            "fats_g": float(meal.fats_g) if meal.fats_g else None,
            "prep_time_min": meal.prep_time_min,
        })

    return {"week_number": week_number, "days": days}


@router.get("/week/{week_number}")
async def get_diet_week(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.user_id == str(current_user.id),
            MealPlan.week_number == week_number,
            MealPlan.is_alternative == False,
            MealPlan.is_active == True,
        ).order_by(MealPlan.day_of_week, MealPlan.meal_type)
    )
    meals = result.scalars().all()
    if not meals:
        raise HTTPException(status_code=404, detail=f"No diet plan for week {week_number}.")

    days = {}
    for meal in meals:
        day = meal.day_of_week
        if day not in days:
            days[day] = []
        days[day].append({
            "id": str(meal.id),
            "meal_type": meal.meal_type,
            "meal_name": meal.meal_name,
            "description": meal.description,
            "calories": meal.calories,
            "protein_g": float(meal.protein_g) if meal.protein_g else None,
            "carbs_g": float(meal.carbs_g) if meal.carbs_g else None,
            "fats_g": float(meal.fats_g) if meal.fats_g else None,
            "prep_time_min": meal.prep_time_min,
        })

    return {"week_number": week_number, "days": days}


@router.post("/generate")
async def generate_diet(
    body: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    week_number = body.week_number or date.today().isocalendar()[1]
    meals = await generate_diet_plan(db, str(current_user.id), week_number)
    return {"message": f"Diet plan generated for week {week_number}", "total_meals": len(meals)}


@router.get("/alternatives/{meal_id}")
async def get_alternatives(
    meal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.alternative_for == meal_id,
            MealPlan.user_id == str(current_user.id),
            MealPlan.is_alternative == True,
        )
    )
    alts = result.scalars().all()

    if not alts:
        # Generate alternatives on the fly
        alts = await generate_alternatives(db, str(current_user.id), meal_id)

    return [
        {
            "id": str(a.id),
            "meal_name": a.meal_name,
            "description": a.description,
            "calories": a.calories,
            "protein_g": float(a.protein_g) if a.protein_g else None,
            "carbs_g": float(a.carbs_g) if a.carbs_g else None,
            "fats_g": float(a.fats_g) if a.fats_g else None,
        }
        for a in alts
    ]


@router.put("/swap/{meal_id}")
async def swap_meal(
    meal_id: str,
    alternative_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Deactivate current meal
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.id == meal_id,
            MealPlan.user_id == str(current_user.id),
        )
    )
    current_meal = result.scalar_one_or_none()
    if not current_meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    current_meal.is_active = False

    # Activate alternative
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.id == alternative_id,
            MealPlan.user_id == str(current_user.id),
        )
    )
    alt_meal = result.scalar_one_or_none()
    if not alt_meal:
        raise HTTPException(status_code=404, detail="Alternative not found")
    alt_meal.is_active = True
    alt_meal.is_alternative = False

    await db.commit()
    return {"message": f"Swapped to {alt_meal.meal_name}"}


@router.get("/recipes/{meal_id}")
async def get_recipe(
    meal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.id == meal_id,
            MealPlan.user_id == str(current_user.id),
        )
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    return {
        "meal_name": meal.meal_name,
        "description": meal.description,
        "recipe": meal.recipe,
        "ingredients": meal.ingredients,
        "calories": meal.calories,
        "protein_g": float(meal.protein_g) if meal.protein_g else None,
        "carbs_g": float(meal.carbs_g) if meal.carbs_g else None,
        "fats_g": float(meal.fats_g) if meal.fats_g else None,
        "fiber_g": float(meal.fiber_g) if meal.fiber_g else None,
        "prep_time_min": meal.prep_time_min,
    }
