from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
import io

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.schemas.progress import DashboardResponse, GraphsResponse, WeeklyReportResponse
from app.services import progress_service
from app.services import achievement_service
from app.utils.progress_card import generate_streak_card, generate_weight_card

router = APIRouter(prefix="/progress", tags=["Progress & Reports"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await progress_service.get_dashboard(db, str(current_user.id), date.today())


@router.get("/graphs", response_model=GraphsResponse)
async def get_graphs(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await progress_service.get_graphs(db, str(current_user.id), days)


@router.get("/streaks")
async def get_streaks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await progress_service.get_streaks(db, str(current_user.id), date.today())


@router.get("/achievements")
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await achievement_service.get_all_achievements(db, str(current_user.id))


@router.post("/achievements/seen")
async def mark_achievements_seen(
    achievement_ids: list[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await achievement_service.mark_seen(db, str(current_user.id), achievement_ids)


@router.get("/share/streak")
async def get_streak_card(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a shareable streak progress card (PDF)."""
    streaks = await progress_service.get_streaks(db, str(current_user.id), date.today())
    pdf_bytes = generate_streak_card(
        user_name=current_user.name,
        current_streak=streaks["current_streak"],
        best_streak=streaks["best_streak"],
        total_active_days=streaks["total_active_days"],
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=streak_card.pdf"},
    )


@router.get("/share/weight")
async def get_weight_card(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a shareable weight progress card (PDF)."""
    result = await db.execute(
        select(HealthProfile).where(HealthProfile.user_id == str(current_user.id))
    )
    profile = result.scalar_one_or_none()
    start_weight = float(profile.weight_kg) if profile else 0

    from app.models.daily_log import DailyLog
    result = await db.execute(
        select(DailyLog.weight_kg).where(
            DailyLog.user_id == str(current_user.id),
            DailyLog.weight_kg.isnot(None),
        ).order_by(DailyLog.log_date.desc()).limit(1)
    )
    row = result.first()
    current_weight = float(row[0]) if row and row[0] else start_weight

    pdf_bytes = generate_weight_card(
        user_name=current_user.name,
        start_weight=start_weight,
        current_weight=current_weight,
        goal=profile.goal if profile else "general_fitness",
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=weight_card.pdf"},
    )


@router.get("/weekly/{week_number}", response_model=WeeklyReportResponse)
async def get_weekly_report(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await progress_service.get_weekly_report(db, str(current_user.id), week_number)


@router.get("/weekly/{week_number}/pdf")
async def get_weekly_report_pdf(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.utils.pdf import generate_report_pdf
    report = await progress_service.get_weekly_report(db, str(current_user.id), week_number)
    pdf_bytes = generate_report_pdf(report, current_user.name)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=week_{week_number}_report.pdf"},
    )
