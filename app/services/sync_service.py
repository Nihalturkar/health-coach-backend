from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sync_queue import SyncQueue
from app.models.daily_log import DailyLog, MealLog, WorkoutLog


async def process_sync_queue(db: AsyncSession, user_id: str, actions: list) -> dict:
    """Process offline actions in client_created_at order."""
    results = {"synced": 0, "failed": 0, "errors": []}

    # Sort by client timestamp
    sorted_actions = sorted(actions, key=lambda a: a.get("client_created_at", ""))

    for action in sorted_actions:
        action_type = action.get("action_type")
        payload = action.get("payload", {})
        client_ts = action.get("client_created_at")

        try:
            if action_type == "log_meal":
                meal = MealLog(user_id=user_id, **payload)
                db.add(meal)

            elif action_type == "log_workout":
                workout = WorkoutLog(user_id=user_id, **payload)
                db.add(workout)

            elif action_type == "log_water":
                log_date = payload.get("log_date")
                water_ml = payload.get("water_ml", 0)
                result = await db.execute(
                    select(DailyLog).where(
                        DailyLog.user_id == user_id,
                        DailyLog.log_date == log_date,
                    )
                )
                daily = result.scalar_one_or_none()
                if daily:
                    daily.water_ml = (daily.water_ml or 0) + water_ml
                else:
                    daily = DailyLog(user_id=user_id, log_date=log_date, water_ml=water_ml)
                    db.add(daily)

            elif action_type == "log_weight":
                log_date = payload.get("log_date")
                weight_kg = payload.get("weight_kg")
                result = await db.execute(
                    select(DailyLog).where(
                        DailyLog.user_id == user_id,
                        DailyLog.log_date == log_date,
                    )
                )
                daily = result.scalar_one_or_none()
                if daily:
                    daily.weight_kg = weight_kg
                else:
                    daily = DailyLog(user_id=user_id, log_date=log_date, weight_kg=weight_kg)
                    db.add(daily)

            elif action_type == "log_sleep":
                log_date = payload.pop("log_date", None)
                if log_date:
                    result = await db.execute(
                        select(DailyLog).where(
                            DailyLog.user_id == user_id,
                            DailyLog.log_date == log_date,
                        )
                    )
                    daily = result.scalar_one_or_none()
                    if daily:
                        for key, value in payload.items():
                            if value is not None:
                                setattr(daily, key, value)
                    else:
                        daily = DailyLog(user_id=user_id, log_date=log_date, **payload)
                        db.add(daily)

            # Save sync record
            sync_record = SyncQueue(
                user_id=user_id,
                action_type=action_type,
                payload=payload,
                client_created_at=client_ts or datetime.now(timezone.utc),
                synced_at=datetime.now(timezone.utc),
                sync_status="synced",
            )
            db.add(sync_record)
            results["synced"] += 1

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"action_type": action_type, "error": str(e)})

            sync_record = SyncQueue(
                user_id=user_id,
                action_type=action_type,
                payload=payload,
                client_created_at=client_ts or datetime.now(timezone.utc),
                sync_status="failed",
                error_message=str(e),
            )
            db.add(sync_record)

    await db.commit()
    return results
