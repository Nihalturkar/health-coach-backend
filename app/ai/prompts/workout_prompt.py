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

## User Feedback (from past workouts)
- Painful/injury-risk exercises (MUST AVOID): {', '.join(profile.get('painful_exercises', [])) or 'none'}
- Too hard exercises (use easier alternatives): {', '.join(profile.get('too_hard_exercises', [])) or 'none'}
- Too easy exercises (increase difficulty/weight): {', '.join(profile.get('too_easy_exercises', [])) or 'none'}

## STRICT Muscle Group Rules (CRITICAL — follow exactly)

workout_type "push" → ONLY exercises for: chest, shoulders, triceps
  - Chest: bench press, push-ups, chest fly, dumbbell press, cable crossover
  - Shoulders: overhead press, lateral raise, front raise, face pull
  - Triceps: tricep dips, skull crushers, rope pushdown, overhead extension

workout_type "pull" → ONLY exercises for: back, biceps, rear delts
  - Back: pull-ups, lat pulldown, barbell row, seated row, deadlift
  - Biceps: barbell curl, dumbbell curl, hammer curl, preacher curl
  - Rear delts: face pull, reverse fly

workout_type "legs" → ONLY exercises for: quads, hamstrings, glutes, calves
  - Quads: squats, leg press, lunges, leg extension, goblet squat
  - Hamstrings: Romanian deadlift, leg curl, stiff-leg deadlift
  - Glutes: hip thrust, glute bridge, Bulgarian split squat, sumo deadlift
  - Calves: calf raises (standing/seated)

workout_type "upper_body" → chest, back, shoulders, biceps, triceps
workout_type "lower_body" → quads, hamstrings, glutes, calves
workout_type "full_body" → one exercise per major group: chest, back, shoulders, legs, core
workout_type "cardio" → running, cycling, jump rope, HIIT, burpees
workout_type "rest" → no exercises, just stretching notes

NEVER put a back exercise in push day. NEVER put a chest exercise in pull day.
NEVER put an arm exercise in legs day. Each exercise's muscle_group MUST match the day type.

## General Rules
1. Each workout day: 5-8 exercises
2. Rest days: mark workout_type as "rest" with no exercises array
3. Include sets, reps (as string like "12" or "8-12" or "30 sec"), rest_seconds
4. Only use exercises possible with available equipment
5. For home workouts without equipment: bodyweight exercises only
6. No same muscle group on consecutive days (except rest/cardio)
7. Include suggested_weight_kg (null for bodyweight exercises)
8. Equipment options: bodyweight, dumbbells, barbell, resistance_bands, pull_up_bar, bench, machine
9. Duration should be 30-60 minutes per session
10. NEVER include painful/injury-risk exercises from feedback
11. Replace "too hard" exercises with easier alternatives targeting the same muscle
12. For "too easy" exercises, add more sets/reps or suggest heavier weights
13. Each exercise MUST have clear step-by-step instructions explaining proper form

## Output Format
Return valid JSON only. No markdown, no explanation. Structure:
{{
  "days": [
    {{
      "day_of_week": 1,
      "workout_type": "push",
      "title": "Push Day - Chest, Shoulders & Triceps",
      "duration_min": 45,
      "location": "{profile.get('workout_location', 'home')}",
      "exercises": [
        {{
          "exercise_name": "Barbell Bench Press",
          "sets": 4,
          "reps": "8-10",
          "rest_seconds": 90,
          "suggested_weight_kg": 40,
          "instructions": "1. Lie flat on bench, grip bar slightly wider than shoulder width. 2. Unrack bar, lower to mid-chest with elbows at 45 degrees. 3. Press up explosively to full lockout. 4. Keep feet flat, back slightly arched, shoulders pinched.",
          "muscle_group": "chest",
          "equipment": "barbell",
          "order_index": 1
        }}
      ]
    }}
  ]
}}

Generate all 7 days. Return only JSON."""
