import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String(50), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
    is_seen = Column(Boolean, default=False)
