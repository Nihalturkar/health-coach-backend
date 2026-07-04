from pydantic import BaseModel
from typing import List, Any, Optional
from datetime import datetime


class SyncAction(BaseModel):
    action_type: str  # log_meal, log_workout, log_water, log_weight, log_sleep
    payload: dict
    client_created_at: datetime


class SyncPushRequest(BaseModel):
    actions: List[SyncAction]


class SyncResult(BaseModel):
    synced: int
    failed: int
    errors: List[Any]
