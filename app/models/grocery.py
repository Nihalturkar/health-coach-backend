import uuid
from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    list_type = Column(String(10), nullable=True)
    week_number = Column(Integer, nullable=True)
    items = Column(JSONB, nullable=False)
    total_estimated_cost = Column(Numeric(8, 2), nullable=True)
    budget_level = Column(String(10), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
