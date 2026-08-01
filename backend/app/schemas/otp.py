from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class OTPResponse(BaseModel):
    id: UUID
    target_id: UUID
    session_id: Optional[UUID] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    body_snippet: Optional[str] = None
    extracted_code: str
    confidence: Optional[str] = None
    received_at: datetime
    is_read: bool

    model_config = {"from_attributes": True}


class OTPBroadcast(BaseModel):
    """WebSocket broadcast payload when a new OTP is captured."""
    type: str = "otp_captured"
    target_email: str
    target_id: str
    session_id: Optional[str] = None
    extracted_code: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    confidence: Optional[str] = None
    captured_at: str
