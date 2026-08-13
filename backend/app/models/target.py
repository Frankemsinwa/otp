import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProviderEnum(str, enum.Enum):
    GMAIL = "GMAIL"
    YAHOO = "YAHOO"
    OTHER = "OTHER"


class TargetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RATE_LIMITED = "RATE_LIMITED"
    IDLE = "IDLE"


class Target(Base):
    __tablename__ = "targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True, index=True)
    provider = Column(Enum(ProviderEnum), default=ProviderEnum.GMAIL, nullable=False)
    status = Column(Enum(TargetStatus), default=TargetStatus.IDLE, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # --- Relationships ---
    credentials = relationship(
        "Credential", back_populates="target", cascade="all, delete-orphan", lazy="selectin"
    )
    sessions = relationship(
        "MonitoringSession", back_populates="target", cascade="all, delete-orphan", lazy="selectin"
    )
    otps = relationship(
        "ReceivedOTP", back_populates="target", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Target {self.email} [{self.provider.value}] status={self.status.value}>"
