"""
Weekly Review Workflow — analyze stats, AI review, adjust plan.

Flow: Collect Stats → Analyze → Compare Targets → AI Review (LLM) → Adjust Plan → Save Report
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.agent import call_groq_json
from app.ai.prompts.review_prompt import get_review_prompt
from app.models.health_profile import HealthProfile
from app.models.progress import WeeklyReport
from app.services.progress_service import generate_weekly_report_data
from app.redis import cache_delete


async def run_weekly_review(db: AsyncSession, user_id: str, week_number: int) -> WeeklyReport:
    """Full weekly review workflow."""

    # --- Node 1: Get Profile ---
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise ValueError("Health profile not found")

    # --- Node 2: Collect Stats from DB ---
    stats = await generate_weekly_report_data(db, user_id, week_number)

    # --- Node 3: Compare vs Targets ---
    profile_data = {
        "goal": profile.goal,
        "target_calories": profile.target_calories,
        "target_protein": profile.target_protein,
        "target_water_ml": profile.target_water_ml,
    }

    # --- Node 4: AI Review (Groq LLM) ---
    prompt = get_review_prompt(profile_data, stats)
    review_data = call_groq_json(
        system_prompt="You are a health coach. Return only valid JSON.",
        user_prompt=prompt,
    )

    # --- Node 5: Adjust Plan ---
    adjustments = review_data.get("plan_adjustments", {})
    cal_change = adjustments.get("calories_change", 0)
    prot_change = adjustments.get("protein_change", 0)

    if cal_change and profile.target_calories:
        new_cal = max(1200, profile.target_calories + cal_change)
        profile.target_calories = new_cal
    if prot_change and profile.target_protein:
        profile.target_protein = max(50, profile.target_protein + prot_change)

    # Invalidate caches so next week gets fresh plan
    await cache_delete(f"meal_plan:{user_id}:{week_number + 1}")

    # --- Node 6: Save Report ---
    result = await db.execute(
        select(WeeklyReport).where(
            WeeklyReport.user_id == user_id,
            WeeklyReport.week_number == week_number,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.start_weight = stats.get("start_weight")
        existing.end_weight = stats.get("end_weight")
        existing.avg_calories_consumed = stats.get("avg_calories_consumed")
        existing.avg_protein_consumed = stats.get("avg_protein_consumed")
        existing.avg_water_ml = stats.get("avg_water_ml")
        existing.avg_sleep_hours = stats.get("avg_sleep_hours")
        existing.workouts_completed = stats.get("workouts_completed")
        existing.workouts_skipped = stats.get("workouts_skipped")
        existing.ai_summary = review_data.get("ai_summary")
        existing.ai_suggestions = review_data.get("ai_suggestions")
        existing.plan_adjustments = adjustments
        report = existing
    else:
        report = WeeklyReport(
            user_id=user_id,
            week_number=week_number,
            start_date=stats["start_date"],
            end_date=stats["end_date"],
            start_weight=stats.get("start_weight"),
            end_weight=stats.get("end_weight"),
            avg_calories_consumed=stats.get("avg_calories_consumed"),
            avg_protein_consumed=stats.get("avg_protein_consumed"),
            avg_water_ml=stats.get("avg_water_ml"),
            avg_sleep_hours=stats.get("avg_sleep_hours"),
            workouts_completed=stats.get("workouts_completed"),
            workouts_skipped=stats.get("workouts_skipped"),
            ai_summary=review_data.get("ai_summary"),
            ai_suggestions=review_data.get("ai_suggestions"),
            plan_adjustments=adjustments,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)
    return report
