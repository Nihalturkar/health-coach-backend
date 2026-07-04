def get_workout_prompt(profile: dict) -> str:
    equipment = ", ".join(profile.get("available_equipment") or ["none"])
    medical = ", ".join(profile.get("medical_conditions") or ["none"])

    split_map = {
        "beginner": "Full Body (3 days workout + 4 rest/stretch days)",
        "intermediate": "Push/Pull/Legs (5 days workout + 2 rest days)",
        "advanced": "Push/Pull/Legs + Cardio (6 days workout + 1 rest day)",
    }
    split = split_map.get(profile.get("fitness_level", "beginner"), split_map["beginner"])

    return f"""You are a certified fitness trainer. Generate a 7-day workout plan.

## User Profile
- Age: {profile['age']}, Gender: {profile['gender']}
- Weight: {profile['weight_kg']} kg, Height: {profile['height_cm']} cm
- Goal: {profile['goal'].replace('_', ' ')}
- Fitness Level: {profile.get('fitness_level', 'beginner')}
- Workout Location: {profile.get('workout_location', 'home')}
- Available Equipment: {equipment}
- Medical Conditions: {medical}

## Training Split
{split}

## Rules
1. Each workout day: 5-8 exercises + warm-up notes + cool-down notes
2. Rest days: mark workout_type as "rest" with optional stretching/yoga
3. Include sets, reps (as string like "12" or "8-12" or "30 sec"), rest_seconds
4. Only use exercises possible with available equipment
5. For home workouts without equipment: bodyweight exercises only
6. No same muscle group on consecutive days (except rest/cardio)
7. Include suggested_weight_kg (null for bodyweight exercises)
8. Muscle groups: chest, back, shoulders, biceps, triceps, quads, hamstrings, glutes, calves, core, full_body
9. Equipment options: bodyweight, dumbbells, barbell, resistance_bands, pull_up_bar, bench, machine
10. Duration should be 30-60 minutes per session

## Output Format
Return valid JSON only. No markdown, no explanation. Structure:
{{
  "days": [
    {{
      "day_of_week": 1,
      "workout_type": "push",
      "title": "Push Day - Chest & Shoulders",
      "duration_min": 45,
      "location": "{profile.get('workout_location', 'home')}",
      "exercises": [
        {{
          "exercise_name": "Push-ups",
          "sets": 3,
          "reps": "12-15",
          "rest_seconds": 60,
          "suggested_weight_kg": null,
          "instructions": "Keep body straight, lower chest to floor, push back up.",
          "muscle_group": "chest",
          "equipment": "bodyweight",
          "order_index": 1
        }}
      ]
    }}
  ]
}}

Generate all 7 days. Return only JSON."""
