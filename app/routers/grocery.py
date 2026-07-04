from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.grocery import GroceryListResponse, GenerateGroceryRequest
from app.services import grocery_service

router = APIRouter(prefix="/grocery", tags=["Grocery"])


@router.get("/weekly", response_model=GroceryListResponse)
async def get_weekly(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await grocery_service.get_weekly_grocery(db, str(current_user.id))


@router.get("/monthly", response_model=GroceryListResponse)
async def get_monthly(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await grocery_service.get_monthly_grocery(db, str(current_user.id))


@router.post("/generate", response_model=GroceryListResponse, status_code=201)
async def generate(
    body: GenerateGroceryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await grocery_service.generate_grocery_list(
        db, str(current_user.id), body.list_type, body.week_number
    )
