"""One-time script to create all tables on production database."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Import all models at module level
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
from app.database import engine, Base


async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created!")
    await engine.dispose()

asyncio.run(create())
