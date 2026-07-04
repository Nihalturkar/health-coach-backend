from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load all models so autogenerate can detect them
from app.database import Base
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

target_metadata = Base.metadata

# Replace asyncpg with psycopg2 for Alembic (Alembic needs sync driver)
def get_url():
    url = os.getenv("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
