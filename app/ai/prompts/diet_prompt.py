def get_diet_prompt(profile: dict) -> str:
    medical = ", ".join(profile.get("medical_conditions") or ["none"])
    allergies = ", ".join(profile.get("allergies") or ["none"])

    return f"""You are a professional Indian nutritionist. Generate a 7-day meal plan.

## User Profile
- Age: {profile['age']}, Gender: {profile['gender']}
- Weight: {profile['weight_kg']} kg, Height: {profile['height_cm']} cm
- Goal: {profile['goal'].replace('_', ' ')}
- Activity Level: {profile['activity_level'].replace('_', ' ')}
- Food Preference: {profile['food_preference'].replace('_', ' ')}
- Budget: {profile['budget_level']}
- Medical Conditions: {medical}
- Allergies: {allergies}

## Targets
- Calories: {profile['target_calories']} kcal/day
- Protein: {profile['target_protein']}g/day
- Carbs: {profile['target_carbs']}g/day
- Fats: {profile['target_fats']}g/day

## Rules
1. Focus on Indian meals (dal, roti, rice, sabzi, etc.)
2. Each day must have: breakfast, mid_morning, lunch, evening_snack, dinner
3. Total daily calories must be within ±100 of target
4. Total daily protein must be within ±10g of target
5. Include prep_time_min for each meal
6. All ingredient quantities must be specific (e.g., "50g", "1 cup", "200ml")
7. If budget is "low", use affordable ingredients; if "high", include premium options
8. Respect food_preference strictly (no meat for veg/vegan)
9. Avoid any items in allergies list
10. For diabetes: reduce refined carbs, prefer low-GI foods
11. For thyroid: limit raw cruciferous vegetables
12. For bp_high: limit sodium, avoid processed foods
13. For pcos: higher protein, lower refined carbs

## Output Format
Return valid JSON only. No markdown, no explanation. Structure:
{{
  "days": [
    {{
      "day_of_week": 1,
      "meals": [
        {{
          "meal_type": "breakfast",
          "meal_name": "Oats with Banana & Almonds",
          "description": "Warm oats topped with banana slices and crushed almonds",
          "calories": 400,
          "protein_g": 15,
          "carbs_g": 55,
          "fats_g": 12,
          "fiber_g": 6,
          "prep_time_min": 10,
          "ingredients": [
            {{"name": "Rolled Oats", "quantity": "50g", "calories": 180}},
            {{"name": "Banana", "quantity": "1 medium", "calories": 100}},
            {{"name": "Almonds", "quantity": "10g", "calories": 60}},
            {{"name": "Milk", "quantity": "200ml", "calories": 60}}
          ],
          "recipe": "1. Boil milk. 2. Add oats, cook 3 min. 3. Top with banana and almonds."
        }}
      ]
    }}
  ]
}}

Generate all 7 days with 5 meals each. Return only JSON."""


def get_alternative_prompt(meal: dict, profile: dict) -> str:
    allergies = ", ".join(profile.get("allergies") or ["none"])
    return f"""Generate 2 alternative meals to replace this meal:

Current meal: {meal['meal_name']} ({meal['calories']} cal, {meal.get('protein_g', 0)}g protein)
Meal type: {meal['meal_type']}
Food preference: {profile['food_preference']}
Allergies: {allergies}
Target calories: ±50 of {meal['calories']}

Return valid JSON only:
{{
  "alternatives": [
    {{
      "meal_name": "...",
      "description": "...",
      "calories": ...,
      "protein_g": ...,
      "carbs_g": ...,
      "fats_g": ...,
      "fiber_g": ...,
      "prep_time_min": ...,
      "ingredients": [{{"name": "...", "quantity": "...", "calories": ...}}],
      "recipe": "..."
    }}
  ]
}}"""
