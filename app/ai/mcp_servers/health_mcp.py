"""
Health MCP Tools — Pure computation functions for health calculations.
No DB access, no LLM calls. Stateless and independently testable.

Used by LangGraph workflow nodes.
"""


def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """Calculate BMI and return numeric value + category string."""
    if height_cm <= 0:
        return {"bmi": 0, "category": "Unknown"}

    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return {"bmi": bmi, "category": category}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation."""
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    elif gender == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr_m = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        bmr_f = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        bmr = (bmr_m + bmr_f) / 2
    return round(bmr, 1)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure."""
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return round(bmr * multipliers.get(activity_level, 1.2), 1)


def calculate_macros(
    tdee: float, goal: str, weight_kg: float, medical_conditions: list = None
) -> dict:
    """Calculate macro targets (calories, protein, carbs, fats) based on goal + medical adjustments."""
    medical_conditions = medical_conditions or []

    # Base calorie target
    calorie_adjustments = {
        "weight_loss": -500,
        "weight_gain": 300,
        "muscle_gain": 200,
        "maintain": 0,
        "general_fitness": 0,
    }
    target_calories = tdee + calorie_adjustments.get(goal, 0)
    target_calories = max(target_calories, 1200)  # safety floor

    # Protein per kg by goal
    protein_per_kg = {
        "weight_loss": 2.0,
        "weight_gain": 1.8,
        "muscle_gain": 2.2,
        "maintain": 1.6,
        "general_fitness": 1.6,
    }
    protein_g = round(weight_kg * protein_per_kg.get(goal, 1.6))

    # Medical adjustments
    if "pcos" in medical_conditions:
        protein_g = round(weight_kg * 2.2)

    # Fat percentage
    fat_pct = 0.30 if goal == "general_fitness" else 0.25
    fats_g = round((target_calories * fat_pct) / 9)

    # Carbs = remaining calories
    protein_cals = protein_g * 4
    fat_cals = fats_g * 9

    if "diabetes" in medical_conditions:
        carb_cals = (target_calories - protein_cals - fat_cals) * 0.85
    else:
        carb_cals = target_calories - protein_cals - fat_cals

    carbs_g = round(max(carb_cals / 4, 50))

    return {
        "target_calories": round(target_calories),
        "target_protein": protein_g,
        "target_carbs": carbs_g,
        "target_fats": fats_g,
    }


def calculate_water(weight_kg: float, activity_level: str) -> int:
    """Calculate daily water intake in ml."""
    water_ml = weight_kg * 35
    if activity_level in ("active", "very_active"):
        water_ml += 500
    return round(water_ml)


def get_ideal_weight(height_cm: float, gender: str) -> float:
    """Calculate ideal weight using Hamwi formula."""
    height_inches = height_cm / 2.54
    inches_over_5ft = max(0, height_inches - 60)

    if gender == "male":
        ideal = 48 + 2.7 * inches_over_5ft
    elif gender == "female":
        ideal = 45.5 + 2.2 * inches_over_5ft
    else:
        ideal_m = 48 + 2.7 * inches_over_5ft
        ideal_f = 45.5 + 2.2 * inches_over_5ft
        ideal = (ideal_m + ideal_f) / 2

    return round(ideal, 1)
