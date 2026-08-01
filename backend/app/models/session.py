import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SessionStatus(str, enum.Enum):
    POLLING = "POLLING"
    ERROR = "ERROR"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"


class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_checked_at = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.POLLING, nullable=False)
    error_log = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0, nullable=False)

    # --- Relationships ---
    target = relationship("Target", back_populates="sessions")
    otps = relationship(
        "ReceivedOTP", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<MonitoringSession target={self.target_id} status={self.status.value}>"
