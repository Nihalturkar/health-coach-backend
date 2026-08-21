"""
Workout MCP Tools — Split determination, exercise validation.
"""

SPLITS = {
    "beginner": {
        "workout_days": 3,
        "rest_days": 4,
        "split_type": "full_body",
        "day_types": ["full_body", "rest", "full_body", "rest", "full_body", "rest", "rest"],
    },
    "intermediate": {
        "workout_days": 5,
        "rest_days": 2,
        "split_type": "push_pull_legs",
        "day_types": ["push", "pull", "legs", "upper_body", "lower_body", "rest", "rest"],
    },
    "advanced": {
        "workout_days": 6,
        "rest_days": 1,
        "split_type": "ppl_cardio",
        "day_types": ["push", "pull", "legs", "push", "pull", "cardio", "rest"],
    },
}


def determine_split(fitness_level: str) -> dict:
    """Return workout split based on fitness level."""
    return SPLITS.get(fitness_level, SPLITS["beginner"])


MUSCLE_GROUPS = {
    "push": ["chest", "shoulders", "triceps"],
    "pull": ["back", "biceps", "rear_delts"],
    "legs": ["quads", "hamstrings", "glutes", "calves"],
    "upper_body": ["chest", "back", "shoulders", "biceps", "triceps"],
    "lower_body": ["quads", "hamstrings", "glutes", "calves"],
    "full_body": ["chest", "back", "shoulders", "quads", "hamstrings", "glutes", "core", "biceps", "triceps"],
    "cardio": ["full_body", "cardio"],
    "rest": [],
}


def validate_workout_day(exercises: list, available_equipment: list, workout_type: str) -> dict:
    """Validate exercises use available equipment and target correct muscles."""
    expected_muscles = set(MUSCLE_GROUPS.get(workout_type, []))
    actual_muscles = {e.get("muscle_group", "").lower() for e in exercises}

    equipment_issues = []
    muscle_issues = []

    for ex in exercises:
        # Check equipment
        eq = ex.get("equipment", "bodyweight")
        if eq != "bodyweight" and eq not in available_equipment:
            equipment_issues.append(f"{ex.get('exercise_name')}: requires {eq}")

        # Check muscle group matches workout type
        mg = ex.get("muscle_group", "").lower()
        if expected_muscles and mg and mg not in expected_muscles and mg != "core":
            muscle_issues.append(
                f"{ex.get('exercise_name')}: muscle '{mg}' doesn't belong in '{workout_type}' day"
            )

    return {
        "passed": len(equipment_issues) == 0 and len(muscle_issues) == 0,
        "equipment_issues": equipment_issues,
        "muscle_issues": muscle_issues,
        "expected_muscles": list(expected_muscles),
        "actual_muscles": list(actual_muscles),
    }


def validate_consecutive_muscles(days: list) -> dict:
    """Check no same muscle group on consecutive workout days."""
    issues = []
    for i in range(1, len(days)):
        prev_type = days[i - 1].get("workout_type", "rest")
        curr_type = days[i].get("workout_type", "rest")
        if prev_type == "rest" or curr_type == "rest":
            continue
        prev_muscles = set(MUSCLE_GROUPS.get(prev_type, []))
        curr_muscles = set(MUSCLE_GROUPS.get(curr_type, []))
        overlap = prev_muscles & curr_muscles
        if overlap:
            issues.append(f"Day {i} and {i+1}: overlapping muscles {overlap}")
    return {"passed": len(issues) == 0, "issues": issues}


def filter_wrong_muscle_exercises(exercises: list, workout_type: str) -> list:
    """Remove exercises whose muscle_group doesn't match the workout_type."""
    expected = set(MUSCLE_GROUPS.get(workout_type, []))
    if not expected:
        return exercises

    filtered = []
    for ex in exercises:
        mg = ex.get("muscle_group", "").lower()
        # Allow core exercises in any day, and keep exercises with matching muscles
        if mg in expected or mg == "core" or not mg:
            filtered.append(ex)
        else:
            print(f"  [FILTER] Removed '{ex.get('exercise_name')}' ({mg}) from {workout_type} day")

    return filtered
