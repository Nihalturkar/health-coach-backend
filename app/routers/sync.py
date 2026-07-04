from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.sync import SyncPushRequest, SyncResult
from app.services import sync_service

router = APIRouter(prefix="/sync", tags=["Offline Sync"])


@router.post("/push", response_model=SyncResult)
async def sync_push(
    body: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actions = [a.model_dump() for a in body.actions]
    return await sync_service.process_sync_queue(db, str(current_user.id), actions)
