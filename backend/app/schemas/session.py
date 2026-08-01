from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.session import SessionStatus


class SessionResponse(BaseModel):
    id: UUID
    target_id: UUID
    status: SessionStatus
    started_at: datetime
    last_checked_at: datetime
    error_log: Optional[str] = None
    consecutive_failures: int = 0

    model_config = {"from_attributes": True}


class SessionStatusUpdate(BaseModel):
    """For internal status transitions."""
    status: SessionStatus
