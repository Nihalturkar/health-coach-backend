"""
Nutrition MCP Tools — Food nutrition lookup and meal validation.
"""

def validate_day_nutrition(meals: list, target_calories: int, target_protein: int) -> dict:
    """Check if a day's meals meet calorie/protein targets. Returns pass/fail + diff."""
    total_cal = sum(m.get("calories", 0) for m in meals)
    total_prot = sum(m.get("protein_g", 0) for m in meals)

    cal_diff = total_cal - target_calories
    prot_diff = total_prot - target_protein

    return {
        "passed": abs(cal_diff) <= 100 and abs(prot_diff) <= 10,
        "total_calories": total_cal,
        "total_protein": round(total_prot, 1),
        "calorie_diff": cal_diff,
        "protein_diff": round(prot_diff, 1),
    }

def adjust_portions(meals: list, target_calories: int) -> list:
    """Programmatically scale meal portions to hit calorie target."""
    total = sum(m.get("calories", 0) for m in meals)
    if total == 0:
        return meals

    ratio = target_calories / total
    adjusted = []
    for meal in meals:
        m = meal.copy()
        m["calories"] = round(m.get("calories", 0) * ratio)
        m["protein_g"] = round(m.get("protein_g", 0) * ratio, 1)
        m["carbs_g"] = round(m.get("carbs_g", 0) * ratio, 1)
        m["fats_g"] = round(m.get("fats_g", 0) * ratio, 1)
        adjusted.append(m)
    return adjusted

MEAL_TYPES_REQUIRED = ["breakfast", "mid_morning", "lunch", "evening_snack", "dinner"]

def validate_meal_coverage(meals: list) -> dict:
    """Check all required meal types are present."""
    types_present = {m.get("meal_type") for m in meals}
    missing = [t for t in MEAL_TYPES_REQUIRED if t not in types_present]
    return {"passed": len(missing) == 0, "missing_types": missing}
