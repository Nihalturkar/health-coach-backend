from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.profile import (
    OnboardingRequest,
    UpdateProfileRequest,
    HealthProfileResponse,
    AssessmentResult,
)
from app.services import health_service

router = APIRouter(prefix="/profile", tags=["Health Profile"])


@router.post("/onboarding", response_model=dict, status_code=201)
async def onboarding(
    body: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await health_service.create_onboarding(
        db, str(current_user.id), body.model_dump()
    )
    return {
        "profile": HealthProfileResponse.model_validate(result["profile"]),
        "assessment": AssessmentResult(**result["assessment"]),
    }


@router.get("", response_model=HealthProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await health_service.get_profile(db, str(current_user.id))


@router.put("", response_model=dict)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    result = await health_service.update_profile(db, str(current_user.id), data)
    return {
        "profile": HealthProfileResponse.model_validate(result["profile"]),
        "assessment": AssessmentResult(**result["assessment"]),
    }


@router.get("/assessment", response_model=AssessmentResult)
async def get_assessment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await health_service.get_assessment(db, str(current_user.id))


@router.post("/reassess", response_model=dict)
async def reassess(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await health_service.reassess(db, str(current_user.id))
    return {
        "profile": HealthProfileResponse.model_validate(result["profile"]),
        "assessment": AssessmentResult(**result["assessment"]),
    }


@router.get("/telegram-status")
async def get_telegram_status(
    current_user: User = Depends(get_current_user),
):
    """Check if Telegram is linked."""
    is_linked = bool(current_user.phone and current_user.phone.startswith("tg:"))
    return {
        "linked": is_linked,
        "telegram_id": current_user.phone.replace("tg:", "") if is_linked else None,
    }


@router.post("/unlink-telegram")
async def unlink_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlink Telegram from this account."""
    current_user.phone = None
    await db.commit()
    return {"message": "Telegram unlinked"}
