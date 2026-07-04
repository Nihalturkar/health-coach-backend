from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.grocery import GroceryList
from app.models.meal_plan import MealPlan
from app.models.health_profile import HealthProfile


async def get_weekly_grocery(db: AsyncSession, user_id: str) -> GroceryList:
    from datetime import date
    week_number = date.today().isocalendar()[1]
    result = await db.execute(
        select(GroceryList).where(
            GroceryList.user_id == user_id,
            GroceryList.list_type == "weekly",
            GroceryList.week_number == week_number,
        ).order_by(GroceryList.created_at.desc())
    )
    grocery = result.scalar_one_or_none()
    if not grocery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No grocery list for this week. Generate one first."
        )
    return grocery


async def get_monthly_grocery(db: AsyncSession, user_id: str) -> GroceryList:
    result = await db.execute(
        select(GroceryList).where(
            GroceryList.user_id == user_id,
            GroceryList.list_type == "monthly",
        ).order_by(GroceryList.created_at.desc())
    )
    grocery = result.scalar_one_or_none()
    if not grocery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No monthly grocery list found. Generate one first."
        )
    return grocery


async def generate_grocery_list(
    db: AsyncSession, user_id: str, list_type: str, week_number: int = None
) -> GroceryList:
    today = date.today()
    week_num = week_number or today.isocalendar()[1]

    # Get health profile for budget
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    budget_level = profile.budget_level if profile else "medium"

    # Get meal plans for this week
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.user_id == user_id,
            MealPlan.week_number == week_num,
            MealPlan.is_alternative == False,
            MealPlan.is_active == True,
        )
    )
    meals = result.scalars().all()

    # Aggregate ingredients from all meals
    ingredient_map = {}
    for meal in meals:
        if meal.ingredients:
            for ing in meal.ingredients:
                name = ing.get("name", "").lower()
                if name and name not in ingredient_map:
                    ingredient_map[name] = {
                        "name": ing.get("name"),
                        "quantity": ing.get("quantity", "as needed"),
                        "category": _categorize_ingredient(name),
                        "est_price": _estimate_price(name, budget_level),
                    }

    items = list(ingredient_map.values())

    # If no meal plan exists yet, return empty list with message
    if not items:
        items = [{"name": "No meal plan found", "quantity": "—", "category": "—", "est_price": 0}]

    total_cost = sum(i.get("est_price") or 0 for i in items)

    grocery = GroceryList(
        user_id=user_id,
        list_type=list_type,
        week_number=week_num if list_type == "weekly" else None,
        items=items,
        total_estimated_cost=round(total_cost, 2),
        budget_level=budget_level,
    )
    db.add(grocery)
    await db.commit()
    await db.refresh(grocery)
    return grocery


def _categorize_ingredient(name: str) -> str:
    grains = ["oats", "rice", "wheat", "bread", "roti", "atta", "poha", "quinoa", "pasta"]
    protein = ["chicken", "egg", "paneer", "dal", "lentil", "fish", "mutton", "tofu", "soy"]
    dairy = ["milk", "curd", "yogurt", "butter", "ghee", "cheese", "whey"]
    vegetables = ["spinach", "broccoli", "tomato", "onion", "garlic", "carrot", "capsicum", "beans"]
    fruits = ["banana", "apple", "mango", "orange", "berries", "pomegranate"]
    fats = ["almond", "walnut", "peanut", "cashew", "olive oil", "coconut"]

    for item in grains:
        if item in name:
            return "grains"
    for item in protein:
        if item in name:
            return "protein"
    for item in dairy:
        if item in name:
            return "dairy"
    for item in vegetables:
        if item in name:
            return "vegetables"
    for item in fruits:
        if item in name:
            return "fruits"
    for item in fats:
        if item in name:
            return "fats & nuts"
    return "other"


def _estimate_price(name: str, budget_level: str) -> float:
    base_prices = {
        "chicken": 200, "egg": 80, "paneer": 120, "milk": 60,
        "oats": 90, "rice": 70, "banana": 40, "apple": 100,
        "spinach": 30, "tomato": 40, "onion": 30, "dal": 100,
    }
    multiplier = {"low": 0.7, "medium": 1.0, "high": 1.4}.get(budget_level, 1.0)
    for key, price in base_prices.items():
        if key in name:
            return round(price * multiplier)
    return round(50 * multiplier)
