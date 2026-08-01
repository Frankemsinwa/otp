import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReceivedOTP(Base):
    __tablename__ = "received_otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("monitoring_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    sender = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    body_snippet = Column(Text, nullable=True)
    extracted_code = Column(String, nullable=False, index=True)
    confidence = Column(String, nullable=True)  # e.g. "0.95"
    received_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    # --- Relationships ---
    target = relationship("Target", back_populates="otps")
    session = relationship("MonitoringSession", back_populates="otps")

    def __repr__(self) -> str:
        return f"<ReceivedOTP code={self.extracted_code} target={self.target_id}>"
