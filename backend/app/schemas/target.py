from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
import re
from app.models.target import ProviderEnum, TargetStatus


def _normalize_phone(v: Optional[str]) -> Optional[str]:
    """Normalize phone numbers to E.164 format (e.g. +14155551234).
    Strips spaces, dashes, parens. Prepends '+' if missing country code marker.
    Returns None for empty/None input. Does not validate fully — just normalizes shape.
    """
    if v is None or v == "":
        return None
    # Strip everything that isn't a digit or leading +
    cleaned = re.sub(r'[^\d+]', '', v.strip())
    if not cleaned:
        return None
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned


class TargetBase(BaseModel):
    email: EmailStr
    phone_number: Optional[str] = None
    provider: ProviderEnum = ProviderEnum.GMAIL

    @field_validator('phone_number', mode='before')
    @classmethod
    def normalize_phone(cls, v):
        return _normalize_phone(v)


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    """Partial update — all fields optional."""
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    provider: Optional[ProviderEnum] = None
    status: Optional[TargetStatus] = None

    @field_validator('phone_number', mode='before')
    @classmethod
    def normalize_phone(cls, v):
        return _normalize_phone(v)


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
