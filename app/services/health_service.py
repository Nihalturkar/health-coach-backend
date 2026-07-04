from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.health_profile import HealthProfile
from app.ai.workflows.assessment import run_assessment


def _run_assessment(profile: HealthProfile) -> dict:
    """Run LangGraph assessment workflow: BMI → BMR → TDEE → Macros → Water → Ideal Weight → AI Summary."""
    result = run_assessment(
        weight_kg=float(profile.weight_kg),
        height_cm=float(profile.height_cm),
        age=profile.age,
        gender=profile.gender,
        activity_level=profile.activity_level,
        goal=profile.goal,
        medical_conditions=profile.medical_conditions or [],
    )
    return {
        "bmi": result["bmi"],
        "bmi_category": result["bmi_category"],
        "bmr": result["bmr"],
        "tdee": result["tdee"],
        "target_calories": result["target_calories"],
        "target_protein": result["target_protein"],
        "target_carbs": result["target_carbs"],
        "target_fats": result["target_fats"],
        "target_water_ml": result["target_water_ml"],
        "ideal_weight_kg": result["ideal_weight_kg"],
        "summary": result.get("summary", ""),
    }


async def create_onboarding(db: AsyncSession, user_id: str, data: dict) -> dict:
    # Check if profile already exists
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists. Use PUT /profile to update."
        )

    profile = HealthProfile(user_id=user_id, **data)
    db.add(profile)
    await db.flush()

    # Run assessment
    assessment = _run_assessment(profile)

    profile.bmi = assessment["bmi"]
    profile.bmr = assessment["bmr"]
    profile.tdee = assessment["tdee"]
    profile.target_calories = assessment["target_calories"]
    profile.target_protein = assessment["target_protein"]
    profile.target_carbs = assessment["target_carbs"]
    profile.target_fats = assessment["target_fats"]
    profile.target_water_ml = assessment["target_water_ml"]
    profile.ideal_weight_kg = assessment["ideal_weight_kg"]

    await db.commit()
    await db.refresh(profile)

    return {"profile": profile, "assessment": assessment}


async def get_profile(db: AsyncSession, user_id: str) -> HealthProfile:
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found. Please complete onboarding first."
        )
    return profile


async def update_profile(db: AsyncSession, user_id: str, data: dict) -> dict:
    profile = await get_profile(db, user_id)

    # Update only provided fields
    for key, value in data.items():
        setattr(profile, key, value)

    # Guard: height and weight must be present for assessment
    if not profile.height_cm or not profile.weight_kg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="height_cm and weight_kg are required for assessment"
        )

    # Re-run assessment after update
    assessment = _run_assessment(profile)

    profile.bmi = assessment["bmi"]
    profile.bmr = assessment["bmr"]
    profile.tdee = assessment["tdee"]
    profile.target_calories = assessment["target_calories"]
    profile.target_protein = assessment["target_protein"]
    profile.target_carbs = assessment["target_carbs"]
    profile.target_fats = assessment["target_fats"]
    profile.target_water_ml = assessment["target_water_ml"]
    profile.ideal_weight_kg = assessment["ideal_weight_kg"]

    await db.commit()
    await db.refresh(profile)

    return {"profile": profile, "assessment": assessment}


async def get_assessment(db: AsyncSession, user_id: str) -> dict:
    profile = await get_profile(db, user_id)
    assessment = _run_assessment(profile)
    return assessment


async def reassess(db: AsyncSession, user_id: str) -> dict:
    profile = await get_profile(db, user_id)
    assessment = _run_assessment(profile)

    profile.bmi = assessment["bmi"]
    profile.bmr = assessment["bmr"]
    profile.tdee = assessment["tdee"]
    profile.target_calories = assessment["target_calories"]
    profile.target_protein = assessment["target_protein"]
    profile.target_carbs = assessment["target_carbs"]
    profile.target_fats = assessment["target_fats"]
    profile.target_water_ml = assessment["target_water_ml"]
    profile.ideal_weight_kg = assessment["ideal_weight_kg"]

    await db.commit()
    await db.refresh(profile)

    return {"profile": profile, "assessment": assessment}
