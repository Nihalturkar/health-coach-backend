from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class GroceryItem(BaseModel):
    name: str
    quantity: str
    category: str
    est_price: Optional[float] = None


class GroceryListResponse(BaseModel):
    id: UUID
    list_type: Optional[str]
    week_number: Optional[int]
    items: List[Any]
    total_estimated_cost: Optional[float]
    budget_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateGroceryRequest(BaseModel):
    list_type: str = "weekly"
    week_number: Optional[int] = None
