from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
import io

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.progress import DashboardResponse, GraphsResponse, WeeklyReportResponse
from app.services import progress_service

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
