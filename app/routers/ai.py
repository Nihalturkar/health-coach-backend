from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timedelta

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.models.daily_log import DailyLog, MealLog, WorkoutLog
from app.models.conversation import Conversation
from app.models.progress import BloodReport
from app.schemas.ai import ChatRequest, ChatResponse, WeeklyReviewRequest
from app.schemas.progress import WeeklyReportResponse
from app.ai.agent import call_groq_chat, call_groq_json
from app.ai.prompts.chat_prompt import get_chat_system_prompt
from app.ai.workflows.weekly_review import run_weekly_review
from app.services.progress_service import get_streaks

router = APIRouter(prefix="/ai", tags=["AI Features"])


async def _get_recent_activity(db: AsyncSession, user_id: str) -> dict:
    """Get today's tracking data for chat context."""
    today = date.today()

    result = await db.execute(
        select(
            func.sum(MealLog.calories).label("cal"),
            func.sum(MealLog.protein_g).label("prot"),
        ).where(MealLog.user_id == user_id, MealLog.log_date == today)
    )
    meal_agg = result.one()

    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == today)
    )
    daily = result.scalar_one_or_none()

    week_start = today - timedelta(days=today.weekday())
    result = await db.execute(
        select(func.count()).select_from(WorkoutLog).where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.log_date >= week_start,
            WorkoutLog.skipped == False,
        )
    )
    workouts_this_week = result.scalar() or 0

    streaks = await get_streaks(db, user_id, today)

    result = await db.execute(
        select(DailyLog.weight_kg).where(
            DailyLog.user_id == user_id,
            DailyLog.weight_kg.isnot(None),
        ).order_by(DailyLog.log_date.desc()).limit(1)
    )
    latest_weight_row = result.first()

    return {
        "calories_today": int(meal_agg.cal or 0),
        "protein_today": round(float(meal_agg.prot or 0), 1),
        "water_ml": daily.water_ml if daily else 0,
        "workouts_this_week": workouts_this_week,
        "current_streak": streaks["current_streak"],
        "latest_weight": float(latest_weight_row[0]) if latest_weight_row and latest_weight_row[0] else None,
    }


async def _get_or_create_conversation(db: AsyncSession, user_id: str) -> Conversation:
    """Get the user's active conversation, or create a new one."""
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc()).limit(1)
    )
    convo = result.scalar_one_or_none()

    if not convo or (datetime.utcnow() - convo.updated_at).total_seconds() > 86400:
        convo = Conversation(user_id=user_id, messages=[], message_count=0)
        db.add(convo)
        await db.commit()
        await db.refresh(convo)

    return convo


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = str(current_user.id)

    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
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

    recent_activity = await _get_recent_activity(db, user_id)
    system_prompt = get_chat_system_prompt(profile_data, recent_activity)

    convo = await _get_or_create_conversation(db, user_id)

    # Build messages from server-side history (last 20 for token limits)
    history_messages = convo.messages or []
    recent_history = history_messages[-20:] if len(history_messages) > 20 else history_messages
    messages = [{"role": m["role"], "content": m["content"]} for m in recent_history]
    messages.append({"role": "user", "content": body.message})

    reply = call_groq_chat(messages, system_prompt)

    # Save to conversation
    now_str = datetime.utcnow().isoformat()
    updated_messages = list(convo.messages or [])
    updated_messages.append({"role": "user", "content": body.message, "timestamp": now_str})
    updated_messages.append({"role": "assistant", "content": reply, "timestamp": now_str})

    convo.messages = updated_messages
    convo.message_count = len(updated_messages)
    await db.commit()

    return ChatResponse(reply=reply)


@router.get("/chat/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for the current conversation."""
    convo = await _get_or_create_conversation(db, str(current_user.id))
    return {
        "conversation_id": str(convo.id),
        "messages": convo.messages or [],
        "message_count": convo.message_count,
    }


@router.delete("/chat/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear chat history — start fresh."""
    convo = await _get_or_create_conversation(db, str(current_user.id))
    convo.messages = []
    convo.message_count = 0
    await db.commit()
    return {"message": "Chat history cleared"}


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
