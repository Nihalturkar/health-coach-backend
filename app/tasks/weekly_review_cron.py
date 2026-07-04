"""
Weekly Review Cron — Runs every Sunday at 21:00.
Generates weekly AI review for all active users who have 5+ days of data.
"""
from datetime import date
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.daily_log import DailyLog
from app.models.health_profile import HealthProfile
from app.ai.workflows.weekly_review import run_weekly_review


async def run_weekly_review_for_all():
    """Run weekly review for all eligible users."""
    print(f"[CRON] Starting weekly review — {date.today()}")

    async with AsyncSessionLocal() as db:
        # Get all active, verified users with health profiles
        result = await db.execute(
            select(User).where(User.is_active == True, User.email_verified == True)
        )
        users = result.scalars().all()

        week_number = date.today().isocalendar()[1]
        reviewed = 0
        skipped = 0

        for user in users:
            # Check if user has a health profile
            profile_result = await db.execute(
                select(HealthProfile).where(HealthProfile.user_id == user.id)
            )
            if not profile_result.scalar_one_or_none():
                skipped += 1
                continue

            # Check if user has at least 5 days of data this week
            week_start = date.today()
            while week_start.weekday() != 0:  # Monday
                from datetime import timedelta
                week_start = week_start - timedelta(days=1)

            log_count_result = await db.execute(
                select(func.count()).select_from(DailyLog).where(
                    DailyLog.user_id == user.id,
                    DailyLog.log_date >= week_start,
                )
            )
            log_count = log_count_result.scalar() or 0

            if log_count < 5:
                skipped += 1
                continue

            try:
                await run_weekly_review(db, str(user.id), week_number)
                reviewed += 1
                print(f"  [OK] {user.email} — week {week_number}")
            except Exception as e:
                print(f"  [FAIL] {user.email} — {e}")

    print(f"[CRON] Weekly review done: {reviewed} reviewed, {skipped} skipped")
