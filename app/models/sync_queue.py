import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action_type = Column(String(30), nullable=False)
    payload = Column(JSONB, nullable=False)
    client_created_at = Column(DateTime, nullable=False)
    synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(10), default="pending")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
