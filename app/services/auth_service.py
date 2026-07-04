from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status
import bcrypt

from app.models.user import User
from app.models.otp_token import OTPToken
from app.models.refresh_token import RefreshToken
from app.utils.email import generate_otp, send_otp_email
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    hash_token,
    get_refresh_token_expiry,
)

OTP_EXPIRE_MINUTES = 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def register_user(db: AsyncSession, name: str, email: str, password: str) -> dict:
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create user
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        email_verified=False,
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    # Delete any old OTPs for this email
    await db.execute(
        delete(OTPToken).where(
            OTPToken.email == email,
            OTPToken.otp_type == "email_verification"
        )
    )

    # Create OTP
    otp_code = generate_otp()
    otp = OTPToken(
        user_id=user.id,
        email=email,
        otp_code=otp_code,
        otp_type="email_verification",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    await db.commit()

    # Send email
    await send_otp_email(email, otp_code, "email_verification")

    return {"message": "Registration successful. Check your email for the OTP.", "debug_otp": otp_code}


async def verify_email(db: AsyncSession, email: str, otp_code: str) -> dict:
    # Find unused, unexpired OTP
    result = await db.execute(
        select(OTPToken).where(
            OTPToken.email == email,
            OTPToken.otp_code == otp_code,
            OTPToken.otp_type == "email_verification",
            OTPToken.is_used == False,
        )
    )
    otp = result.scalar_one_or_none()

    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    if otp.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )

    # Mark OTP used
    otp.is_used = True

    # Activate user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.email_verified = True
    await db.commit()
    await db.refresh(user)

    # Issue tokens
    access_token = create_access_token(str(user.id))
    raw_refresh, hashed_refresh = create_refresh_token()

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=get_refresh_token_expiry(),
    )
    db.add(refresh_token_row)
    await db.commit()

    return {"access_token": access_token, "refresh_token": raw_refresh, "user": user}


async def quick_register(db: AsyncSession, name: str, email: str, password: str) -> dict:
    """Register + auto-verify + return tokens in one step. No OTP needed."""
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        email_verified=True,
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token(str(user.id))
    raw_refresh, hashed_refresh = create_refresh_token()

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=get_refresh_token_expiry(),
    )
    db.add(refresh_token_row)
    await db.commit()
    await db.refresh(user)

    return {"access_token": access_token, "refresh_token": raw_refresh, "user": user}


async def login_user(db: AsyncSession, email: str, password: str) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    access_token = create_access_token(str(user.id))
    raw_refresh, hashed_refresh = create_refresh_token()

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=get_refresh_token_expiry(),
    )
    db.add(refresh_token_row)
    await db.commit()

    return {"access_token": access_token, "refresh_token": raw_refresh, "user": user}


async def refresh_access_token(db: AsyncSession, raw_refresh_token: str) -> dict:
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
        )
    )
    token_row = result.scalar_one_or_none()

    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if token_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired. Please login again."
        )

    # Rotate: revoke old, issue new
    token_row.is_revoked = True

    result = await db.execute(select(User).where(User.id == token_row.user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token(str(user.id))
    new_raw_refresh, new_hashed_refresh = create_refresh_token()

    new_refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=new_hashed_refresh,
        expires_at=get_refresh_token_expiry(),
    )
    db.add(new_refresh_row)
    await db.commit()

    return {"access_token": new_access, "refresh_token": new_raw_refresh, "user": user}


async def logout_user(db: AsyncSession, raw_refresh_token: str) -> dict:
    token_hash = hash_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()
    if token_row:
        token_row.is_revoked = True
        await db.commit()
    return {"message": "Logged out successfully"}


async def resend_otp(db: AsyncSession, email: str, otp_type: str) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If this email is registered, an OTP has been sent."}

    if otp_type == "email_verification" and user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    # Delete old OTPs
    await db.execute(
        delete(OTPToken).where(
            OTPToken.email == email,
            OTPToken.otp_type == otp_type
        )
    )

    otp_code = generate_otp()
    otp = OTPToken(
        user_id=user.id,
        email=email,
        otp_code=otp_code,
        otp_type=otp_type,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    await db.commit()

    await send_otp_email(email, otp_code, otp_type)
    return {"message": "If this email is registered, an OTP has been sent."}


async def forgot_password(db: AsyncSession, email: str) -> dict:
    return await resend_otp(db, email, "password_reset")


async def reset_password(db: AsyncSession, email: str, otp_code: str, new_password: str) -> dict:
    result = await db.execute(
        select(OTPToken).where(
            OTPToken.email == email,
            OTPToken.otp_code == otp_code,
            OTPToken.otp_type == "password_reset",
            OTPToken.is_used == False,
        )
    )
    otp = result.scalar_one_or_none()

    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    if otp.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )

    otp.is_used = True

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(new_password)

    # Revoke all refresh tokens on password reset
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user.id)
    )

    await db.commit()
    return {"message": "Password reset successful. Please login with your new password."}


async def delete_account(db: AsyncSession, user_id: str) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "Account deleted successfully"}
