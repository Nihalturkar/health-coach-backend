"""
Auto-run script to create all tables on production database.
Called by Procfile before uvicorn starts.
Uses CREATE TABLE IF NOT EXISTS — safe to run on every deploy.
"""
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

# Import all models so Base.metadata knows about them
from app.models.user import User
from app.models.otp_token import OTPToken
from app.models.refresh_token import RefreshToken
from app.models.health_profile import HealthProfile
from app.models.notification_preference import NotificationPreference
from app.models.meal_plan import MealPlan
from app.models.workout_plan import WorkoutPlan, WorkoutExercise
from app.models.daily_log import DailyLog, MealLog, WorkoutLog
from app.models.progress import ProgressPhoto, WeeklyReport, BloodReport
from app.models.notification import Notification
from app.models.sync_queue import SyncQueue
from app.models.grocery import GroceryList
from app.models.achievement import Achievement
from app.models.conversation import Conversation
from app.models.exercise_log import ExerciseLog
from app.models.feedback import MealFeedback, ExerciseFeedback
from app.database import engine, Base


async def create():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[CREATE_TABLES] All tables created/verified successfully!")
    except Exception as e:
        print(f"[CREATE_TABLES] Error: {e}")
        print("[CREATE_TABLES] Continuing anyway — tables may already exist.")
    finally:
        await engine.dispose()


try:
    asyncio.run(create())
except Exception as e:
    print(f"[CREATE_TABLES] Fatal: {e}")
    # Don't exit with error code — let uvicorn start anyway
    # Tables might already exist from a previous deploy
    print("[CREATE_TABLES] Skipping table creation, starting server...")
