"""
OTP Cleanup Cron — Runs daily.
Deletes expired and used OTP tokens to keep the table clean.
"""
from datetime import datetime, timezone
from sqlalchemy import delete, or_
from app.database import AsyncSessionLocal
from app.models.otp_token import OTPToken


async def cleanup_expired_otps():
    """Delete expired and used OTP tokens."""
    print(f"[CRON] OTP cleanup started — {datetime.now(timezone.utc)}")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(OTPToken).where(
                or_(
                    OTPToken.expires_at < datetime.now(timezone.utc),
                    OTPToken.is_used == True,
                )
            )
        )
        await db.commit()

        deleted = result.rowcount
        print(f"[CRON] OTP cleanup done: {deleted} tokens deleted")
