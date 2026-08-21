"""
Reminder Cron — Runs every hour.
Checks user notification preferences and sends reminders for:
  - Meals (at user-configured times)
  - Workouts (at user-configured time)
  - Water (every N hours based on preference)
  - Weigh-in (at user-configured time)
"""
from datetime import date, datetime, timedelta
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.notification_preference import NotificationPreference
from app.models.notification import Notification
from app.models.daily_log import DailyLog, MealLog, WorkoutLog
from app.utils.firebase import send_push_notification


def _current_hour_str() -> str:
    """Return current hour as 'HH:00' string."""
    return datetime.now().strftime("%H:00")


def _time_matches(configured_time: str, tolerance_min: int = 30) -> bool:
    """Check if current time is within tolerance of configured time (HH:MM)."""
    try:
        now = datetime.now()
        hour, minute = map(int, configured_time.split(":"))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        diff = abs((now - target).total_seconds())
        return diff <= tolerance_min * 60
    except (ValueError, AttributeError):
        return False


async def _save_and_send(
    db, user_id, fcm_token, notif_type, title, body, data=None
):
    """Save notification to DB and send via FCM."""
    now = datetime.now()

    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        body=body,
        data=data,
        scheduled_at=now,
        sent_at=now,
    )
    db.add(notif)

    if fcm_token:
        await send_push_notification(fcm_token, title, body, data or {})


async def run_reminders():
    """Main reminder loop — called every hour by scheduler."""
    print(f"[CRON] Running reminders — {datetime.now().strftime('%H:%M')}")

    async with AsyncSessionLocal() as db:
        # Get all users with notification preferences and FCM tokens
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.fcm_token.isnot(None)
            )
        )
        prefs_list = result.scalars().all()

        sent_count = 0
        today = date.today()

        for prefs in prefs_list:
            user_id = str(prefs.user_id)
            fcm_token = prefs.fcm_token

            # --- Meal Reminders ---
            if prefs.meal_reminders and prefs.meal_reminder_times:
                for meal_time in prefs.meal_reminder_times:
                    if _time_matches(meal_time):
                        # Check if user already logged a meal in the last 2 hours
                        two_hours_ago = datetime.now() - timedelta(hours=2)
                        result = await db.execute(
                            select(MealLog).where(
                                MealLog.user_id == user_id,
                                MealLog.log_date == today,
                                MealLog.created_at >= two_hours_ago,
                            ).limit(1)
                        )
                        if not result.scalar_one_or_none():
                            await _save_and_send(
                                db, user_id, fcm_token,
                                "meal_reminder",
                                "Time to eat! 🍽️",
                                "Don't forget to log your meal to keep your streak going.",
                                {"action": "log_meal"},
                            )
                            sent_count += 1

            # --- Workout Reminder ---
            if prefs.workout_reminders and prefs.workout_reminder_time:
                if _time_matches(prefs.workout_reminder_time):
                    # Check if user already logged workout today
                    result = await db.execute(
                        select(WorkoutLog).where(
                            WorkoutLog.user_id == user_id,
                            WorkoutLog.log_date == today,
                        ).limit(1)
                    )
                    if not result.scalar_one_or_none():
                        await _save_and_send(
                            db, user_id, fcm_token,
                            "workout_reminder",
                            "Workout time! 💪",
                            "Your workout is waiting. Let's keep the momentum!",
                            {"action": "start_workout"},
                        )
                        sent_count += 1

            # --- Water Reminder ---
            if prefs.water_reminders and prefs.water_reminder_interval_hours:
                interval = prefs.water_reminder_interval_hours
                current_hour = datetime.now().hour
                # Send water reminders during waking hours (7 AM - 10 PM)
                if 7 <= current_hour <= 22 and current_hour % interval == 0:
                    # Check today's water intake
                    result = await db.execute(
                        select(DailyLog).where(
                            DailyLog.user_id == user_id,
                            DailyLog.log_date == today,
                        )
                    )
                    daily = result.scalar_one_or_none()
                    water_ml = daily.water_ml if daily else 0

                    if water_ml < 2500:  # Only remind if under reasonable target
                        glasses = round(water_ml / 250)
                        await _save_and_send(
                            db, user_id, fcm_token,
                            "water_reminder",
                            "Stay hydrated! 💧",
                            f"You've had {glasses} glasses today. Have another glass of water!",
                            {"action": "log_water"},
                        )
                        sent_count += 1

            # --- Weigh-in Reminder ---
            if prefs.weigh_in_reminder and prefs.weigh_in_time:
                if _time_matches(prefs.weigh_in_time):
                    # Check if user already logged weight today
                    result = await db.execute(
                        select(DailyLog).where(
                            DailyLog.user_id == user_id,
                            DailyLog.log_date == today,
                            DailyLog.weight_kg.isnot(None),
                        ).limit(1)
                    )
                    if not result.scalar_one_or_none():
                        await _save_and_send(
                            db, user_id, fcm_token,
                            "weighin_reminder",
                            "Morning weigh-in ⚖️",
                            "Log your weight to track your progress!",
                            {"action": "log_weight"},
                        )
                        sent_count += 1

        await db.commit()
        print(f"[CRON] Reminders done: {sent_count} sent to {len(prefs_list)} users")
