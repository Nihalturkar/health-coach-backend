from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    VerifyEmailRequest,
    LoginRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendOTPRequest,
    UpdateProfileRequest,
    AuthResponse,
    UserResponse,
    MessageResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, body.name, body.email, body.password)


@router.post("/quick-register", response_model=AuthResponse, status_code=201)
async def quick_register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.quick_register(db, body.name, body.email, body.password)
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse.model_validate(result["user"]),
    )


@router.post("/verify-email", response_model=AuthResponse)
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.verify_email(db, body.email, body.otp)
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse.model_validate(result["user"]),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.login_user(db, body.email, body.password)
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse.model_validate(result["user"]),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.refresh_access_token(db, body.refresh_token)
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse.model_validate(result["user"]),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.logout_user(db, body.refresh_token)


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(body: ResendOTPRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.resend_otp(db, body.email, body.otp_type)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.forgot_password(db, body.email)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.reset_password(db, body.email, body.otp, body.new_password)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/update-profile", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.name = body.name
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/delete-account", response_model=MessageResponse)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.delete_account(db, current_user.id)
