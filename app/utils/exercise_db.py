"""
ExerciseDB API client — Fetch exercise GIFs, instructions, muscle groups.
Uses RapidAPI ExerciseDB endpoint.
"""
import httpx
from app.config import settings
from app.redis import cache_get, cache_set

EXERCISE_DB_URL = "https://exercisedb.p.rapidapi.com"


async def get_exercise_by_name(exercise_name: str) -> dict | None:
    """Search ExerciseDB for an exercise and return details with GIF URL."""
    if not settings.EXERCISE_DB_API_KEY:
        return None

    # Check cache first
    cache_key = f"exercise:{exercise_name.lower().replace(' ', '_')}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{EXERCISE_DB_URL}/exercises/name/{exercise_name}",
                headers={
                    "X-RapidAPI-Key": settings.EXERCISE_DB_API_KEY,
                    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
                },
                params={"limit": "1"},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if not data:
                return None

            exercise = data[0]
            result = {
                "name": exercise.get("name"),
                "gif_url": exercise.get("gifUrl"),
                "body_part": exercise.get("bodyPart"),
                "target": exercise.get("target"),
                "equipment": exercise.get("equipment"),
                "instructions": exercise.get("instructions", []),
                "secondary_muscles": exercise.get("secondaryMuscles", []),
            }

            # Cache for 7 days
            await cache_set(cache_key, result, ttl_seconds=7 * 24 * 3600)
            return result

    except Exception as e:
        print(f"ExerciseDB API error: {e}")
        return None


async def search_exercises(query: str, limit: int = 10) -> list:
    """Search exercises by name."""
    if not settings.EXERCISE_DB_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{EXERCISE_DB_URL}/exercises/name/{query}",
                headers={
                    "X-RapidAPI-Key": settings.EXERCISE_DB_API_KEY,
                    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
                },
                params={"limit": str(limit)},
            )

            if response.status_code != 200:
                return []

            return [
                {
                    "name": ex.get("name"),
                    "gif_url": ex.get("gifUrl"),
                    "body_part": ex.get("bodyPart"),
                    "target": ex.get("target"),
                    "equipment": ex.get("equipment"),
                }
                for ex in response.json()
            ]
    except Exception as e:
        print(f"ExerciseDB search error: {e}")
        return []
