import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)  # Fernet-encrypted at rest
    oauth_access_token = Column(Text, nullable=True)    # Fernet-encrypted at rest
    token_expiry = Column(DateTime, nullable=True)
    captured_at = Column(DateTime, server_default=func.now(), nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # --- Relationship ---
    target = relationship("Target", back_populates="credentials")

    def __repr__(self) -> str:
        return f"<Credential user={self.username} target={self.target_id}>"
