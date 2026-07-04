from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.models.progress import BloodReport
from app.schemas.ai import ChatRequest, ChatResponse, WeeklyReviewRequest
from app.schemas.progress import WeeklyReportResponse
from app.ai.agent import call_groq_chat, call_groq_json
from app.ai.prompts.chat_prompt import get_chat_system_prompt
from app.ai.workflows.weekly_review import run_weekly_review

router = APIRouter(prefix="/ai", tags=["AI Features"])


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == str(current_user.id))
    )
    profile = result.scalar_one_or_none()

    profile_data = {}
    if profile:
        profile_data = {
            "age": profile.age,
            "gender": profile.gender,
            "weight_kg": float(profile.weight_kg),
            "height_cm": float(profile.height_cm),
            "bmi": float(profile.bmi) if profile.bmi else None,
            "goal": profile.goal,
            "activity_level": profile.activity_level,
            "food_preference": profile.food_preference,
            "medical_conditions": profile.medical_conditions or [],
            "allergies": profile.allergies or [],
            "target_calories": profile.target_calories,
            "target_protein": profile.target_protein,
        }

    system_prompt = get_chat_system_prompt(profile_data)

    messages = [{"role": m.role, "content": m.content} for m in (body.history or [])]
    messages.append({"role": "user", "content": body.message})

    reply = call_groq_chat(messages, system_prompt)
    return ChatResponse(reply=reply)


@router.post("/weekly-review", response_model=WeeklyReportResponse)
async def weekly_review(
    body: WeeklyReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    week_number = body.week_number or date.today().isocalendar()[1]
    report = await run_weekly_review(db, str(current_user.id), week_number)
    return report


@router.post("/analyze-blood-report")
async def analyze_blood_report(
    report_text: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze blood report text and return health insights."""
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == str(current_user.id))
    )
    profile = result.scalar_one_or_none()

    medical = ", ".join(profile.medical_conditions or ["none"]) if profile else "none"
    goal = profile.goal.replace("_", " ") if profile else "general fitness"

    prompt = f"""Analyze this blood report data and provide health insights.

User's goal: {goal}
Medical conditions: {medical}

Blood Report Data:
{report_text}

Return valid JSON:
{{
  "extracted_data": {{"hemoglobin": null, "vitamin_d": null, "b12": null, "thyroid_tsh": null, "cholesterol": null, "blood_sugar_fasting": null}},
  "ai_analysis": {{"overall_status": "good/average/needs_attention", "key_findings": ["finding1", "finding2"], "concerns": ["concern1"]}},
  "ai_suggestions": [
    {{"area": "diet", "suggestion": "specific suggestion"}},
    {{"area": "supplement", "suggestion": "specific suggestion"}}
  ]
}}

Fill extracted_data with actual values from the report where available. Return only JSON."""

    analysis = call_groq_json(
        system_prompt="You are a health analyst. Analyze blood reports and give actionable insights. Return only valid JSON.",
        user_prompt=prompt,
    )

    # Save report
    blood_report = BloodReport(
        user_id=str(current_user.id),
        report_url="text_input",
        report_date=date.today(),
        extracted_data=analysis.get("extracted_data"),
        ai_analysis=analysis.get("ai_analysis"),
        ai_suggestions=analysis.get("ai_suggestions"),
    )
    db.add(blood_report)
    await db.commit()
    await db.refresh(blood_report)

    return {
        "id": str(blood_report.id),
        "extracted_data": analysis.get("extracted_data"),
        "ai_analysis": analysis.get("ai_analysis"),
        "ai_suggestions": analysis.get("ai_suggestions"),
    }
