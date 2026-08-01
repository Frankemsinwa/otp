from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.target import ProviderEnum, TargetStatus


class TargetBase(BaseModel):
    email: EmailStr
    provider: ProviderEnum = ProviderEnum.GMAIL


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    """Partial update — all fields optional."""
    email: Optional[EmailStr] = None
    provider: Optional[ProviderEnum] = None
    status: Optional[TargetStatus] = None


class TargetResponse(TargetBase):
    id: UUID
    status: TargetStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TargetDetailResponse(TargetResponse):
    """Extended response with relationship counts."""
    credential_count: int = 0
    session_count: int = 0
    otp_count: int = 0

    model_config = {"from_attributes": True}
