"""
ExerciseDB API client — Fetch exercise GIFs, instructions, muscle groups.
Uses free ExerciseDB API (oss.exercisedb.dev) — no API key needed.

GIFs are high-quality animated demonstrations of proper exercise form.
"""
import httpx
from app.redis import cache_get, cache_set

FREE_EXERCISE_DB_URL = "https://oss.exercisedb.dev/api/v1"


# Common exercise name mappings (LLM output → ExerciseDB name)
NAME_ALIASES = {
    "barbell bench press": "barbell bench press",
    "bench press": "barbell bench press",
    "flat bench press": "barbell bench press",
    "incline bench press": "barbell incline bench press",
    "dumbbell bench press": "dumbbell bench press",
    "dumbbell press": "dumbbell bench press",
    "push-ups": "push-up",
    "push ups": "push-up",
    "pushups": "push-up",
    "pull-ups": "pull-up",
    "pull ups": "pull-up",
    "pullups": "pull-up",
    "chin-ups": "chin-up",
    "chin ups": "chin-up",
    "lat pulldown": "cable lat pulldown",
    "barbell row": "barbell bent over row",
    "bent over row": "barbell bent over row",
    "dumbbell row": "dumbbell bent over row",
    "overhead press": "barbell standing military press",
    "military press": "barbell standing military press",
    "shoulder press": "dumbbell shoulder press",
    "lateral raise": "dumbbell lateral raise",
    "lateral raises": "dumbbell lateral raise",
    "front raise": "dumbbell front raise",
    "bicep curl": "barbell curl",
    "bicep curls": "barbell curl",
    "barbell curl": "barbell curl",
    "dumbbell curl": "dumbbell biceps curl",
    "hammer curl": "dumbbell hammer curl",
    "hammer curls": "dumbbell hammer curl",
    "tricep dips": "triceps dip",
    "tricep pushdown": "cable pushdown",
    "rope pushdown": "cable rope pushdown",
    "skull crushers": "barbell lying triceps extension skull crusher",
    "squats": "barbell full squat",
    "barbell squat": "barbell full squat",
    "goblet squat": "dumbbell goblet squat",
    "lunges": "barbell lunge",
    "dumbbell lunges": "dumbbell lunge",
    "leg press": "sled leg press",
    "leg extension": "lever leg extension",
    "leg curl": "lever lying leg curl",
    "romanian deadlift": "barbell romanian deadlift",
    "rdl": "barbell romanian deadlift",
    "deadlift": "barbell deadlift",
    "hip thrust": "barbell hip thrust",
    "glute bridge": "barbell glute bridge",
    "calf raises": "barbell standing calf raise",
    "calf raise": "barbell standing calf raise",
    "standing calf raise": "barbell standing calf raise",
    "plank": "front plank",
    "crunches": "crunch",
    "sit-ups": "sit-up",
    "sit ups": "sit-up",
    "russian twist": "russian twist",
    "face pull": "cable face pull",
    "face pulls": "cable face pull",
    "cable fly": "cable standing fly",
    "chest fly": "dumbbell fly",
    "dumbbell fly": "dumbbell fly",
    "incline dumbbell press": "dumbbell incline bench press",
    "preacher curl": "barbell preacher curl",
    "concentration curl": "dumbbell concentration curl",
    "bulgarian split squat": "dumbbell bulgarian split squat",
    "sumo deadlift": "barbell sumo deadlift",
    "cable crossover": "cable crossover",
    "chest dip": "chest dip",
    "dips": "chest dip",
    "burpees": "burpee",
    "mountain climbers": "mountain climber",
    "jumping jacks": "jumping jack",
    "jump rope": "jump rope",
}


def _normalize_name(name: str) -> str:
    """Normalize exercise name for better ExerciseDB matching."""
    lower = name.lower().strip()
    return NAME_ALIASES.get(lower, lower)


async def get_exercise_by_name(exercise_name: str) -> dict | None:
    """Search ExerciseDB for an exercise by name and return details with GIF URL."""
    normalized = _normalize_name(exercise_name)
    cache_key = f"edb:{normalized.replace(' ', '_')}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try exact name first
            response = await client.get(
                f"{FREE_EXERCISE_DB_URL}/exercises",
                params={"name": normalized, "limit": "3"},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            exercises = data.get("data", [])

            # Find best match — prefer exact name match
            exercise = None
            for ex in exercises:
                if ex.get("name", "").lower() == normalized:
                    exercise = ex
                    break
            if not exercise and exercises:
                exercise = exercises[0]

            if not exercise:
                # Try with original name as fallback
                if normalized != exercise_name.lower():
                    response = await client.get(
                        f"{FREE_EXERCISE_DB_URL}/exercises",
                        params={"name": exercise_name, "limit": "1"},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        exercises = data.get("data", [])
                        if exercises:
                            exercise = exercises[0]

            if not exercise:
                return None

            result = {
                "name": exercise.get("name"),
                "gif_url": exercise.get("gifUrl"),
                "body_parts": exercise.get("bodyParts", []),
                "target_muscles": exercise.get("targetMuscles", []),
                "equipments": exercise.get("equipments", []),
                "instructions": exercise.get("instructions", []),
                "secondary_muscles": exercise.get("secondaryMuscles", []),
            }

            # Cache for 7 days
            await cache_set(cache_key, result, ttl_seconds=7 * 24 * 3600)
            return result

    except Exception as e:
        print(f"ExerciseDB API error: {e}")
        return None


async def enrich_exercises_with_gifs(exercises: list[dict]) -> list[dict]:
    """Batch enrich a list of exercises with GIF URLs and instructions from ExerciseDB."""
    for ex in exercises:
        name = ex.get("exercise_name", "")
        if not name:
            continue

        edb = await get_exercise_by_name(name)
        if edb:
            if edb.get("gif_url"):
                ex["gif_url"] = edb["gif_url"]
            # Also enrich with ExerciseDB's detailed instructions if our prompt ones are short
            if edb.get("instructions") and len(edb["instructions"]) > 0:
                existing = ex.get("instructions", "")
                if not existing or len(existing) < 50:
                    ex["instructions"] = " ".join(edb["instructions"])

    return exercises


async def search_exercises(query: str, limit: int = 10) -> list:
    """Search exercises by name."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{FREE_EXERCISE_DB_URL}/exercises",
                params={"name": query, "limit": str(limit)},
            )

            if response.status_code != 200:
                return []

            data = response.json()
            return [
                {
                    "name": ex.get("name"),
                    "gif_url": ex.get("gifUrl"),
                    "body_parts": ex.get("bodyParts", []),
                    "target_muscles": ex.get("targetMuscles", []),
                    "equipments": ex.get("equipments", []),
                }
                for ex in data.get("data", [])
            ]
    except Exception as e:
        print(f"ExerciseDB search error: {e}")
        return []
