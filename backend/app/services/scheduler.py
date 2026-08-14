"""
Background polling scheduler.
Manages an asyncio Task per active MonitoringSession.
Handles exponential backoff, fetching, extracting, and broadcasting.

Stealth features:
- Jittered polling intervals (±25% by default)
- IMAP IDLE for Yahoo (real-time push, reduces polling fingerprint)
- Proxy rotation per target
- Rate limit awareness with Retry-After respect
- OAuth client rotation
"""
import asyncio
import random
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import decrypt_token, decrypt_password
from app.models.session import MonitoringSession, SessionStatus
from app.models.target import Target, ProviderEnum
from app.models.credential import Credential
from app.models.otp import ReceivedOTP
from app.services.extractor import OTPExtractor
from app.services.email.gmail import GmailService
from app.services.email.yahoo import YahooService
from app.core.logging import get_logger
from app.api.websocket import manager as ws_manager

log = get_logger("services.scheduler")

# Track active tasks: mapping of session_id (str) -> asyncio.Task
_active_tasks: Dict[str, asyncio.Task] = {}


async def start_polling_task(session_id: UUID) -> None:
    """Launch a background polling loop for a specific session."""
    session_str = str(session_id)
    if session_str in _active_tasks and not _active_tasks[session_str].done():
        log.warning(f"Polling task for session {session_str} is already running.")
        return

    task = asyncio.create_task(_polling_loop(session_id))
    _active_tasks[session_str] = task
    log.info(f"Started polling task for session {session_str}")


async def stop_polling_task(session_id: UUID) -> None:
    """Cancel a running polling loop."""
    session_str = str(session_id)
    task = _active_tasks.get(session_str)
    if task and not task.done():
        task.cancel()
        log.info(f"Cancelled polling task for session {session_str}")
    _active_tasks.pop(session_str, None)


async def shutdown_all() -> None:
    """Cancel all running tasks on app shutdown."""
    for session_str, task in _active_tasks.items():
        if not task.done():
            task.cancel()
    _active_tasks.clear()
    log.info("All polling tasks shut down.")


async def _polling_loop(session_id: UUID) -> None:
    """The actual infinite loop that polls for emails and extracts OTPs."""
    extractor = OTPExtractor()
    yahoo_service: Optional[YahooService] = None
    idle_started = False
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # 1. Fetch session and target data
                session = await _get_session_data(db, session_id)
                if not session or session.status != SessionStatus.POLLING:
                    log.info(f"Stopping loop for {session_id} - status is {session.status if session else 'deleted'}")
                    break

                target = session.target
                credential = target.credentials[0] if target.credentials else None

                if not credential:
                    log.error(f"No credentials found for target {target.id}")
                    await _mark_session_error(db, session, "Missing credentials")
                    break

                # 2. Authenticate and Fetch
                messages = []
                if target.provider == ProviderEnum.GMAIL:
                    access = decrypt_token(credential.oauth_access_token) if credential.oauth_access_token else None
                    refresh = decrypt_token(credential.oauth_refresh_token) if credential.oauth_refresh_token else None
                    service = GmailService({
                        "oauth_access_token": access, 
                        "oauth_refresh_token": refresh,
                        "target_email": target.email
                    })
                    
                    if await service.authenticate():
                        # Save refreshed token if it changed
                        new_token = service.get_refreshed_token()
                        if new_token and new_token != access:
                            from app.core.security import encrypt_token
                            credential.oauth_access_token = encrypt_token(new_token)
                            await db.commit()
                        
                        messages = await service.fetch_recent_messages()
                    else:
                        raise ValueError("Gmail authentication failed")

                elif target.provider == ProviderEnum.YAHOO:
                    access = decrypt_token(credential.oauth_access_token) if credential.oauth_access_token else None
                    refresh = decrypt_token(credential.oauth_refresh_token) if credential.oauth_refresh_token else None
                    
                    # Reuse Yahoo service instance for IDLE persistence
                    if yahoo_service is None:
                        yahoo_service = YahooService({
                            "username": credential.username,
                            "oauth_access_token": access,
                            "oauth_refresh_token": refresh,
                            "target_email": target.email
                        })
                    else:
                        # Update tokens if they changed
                        yahoo_service.access_token = access
                        yahoo_service.refresh_token = refresh

                    if await yahoo_service.authenticate():
                        # Save refreshed token if it changed
                        new_token = yahoo_service.get_refreshed_token()
                        if new_token and new_token != access:
                            from app.core.security import encrypt_token
                            credential.oauth_access_token = encrypt_token(new_token)
                            await db.commit()

                        # Try to start IDLE for real-time push (reduces polling fingerprint)
                        if settings.USE_IMAP_IDLE and not idle_started:
                            async def on_new_mail(new_messages):
                                # Process new messages immediately
                                for msg in new_messages:
                                    msg_id = msg.get("id")
                                    if msg_id:
                                        existing_otp = await db.execute(
                                            select(ReceivedOTP).filter_by(target_id=target.id, message_id=msg_id)
                                        )
                                        if existing_otp.scalars().first():
                                            continue
                                    
                                    codes = extractor.extract_all_codes(msg["subject"], msg["body"], msg["sender"])
                                    if codes:
                                        best_code, confidence = codes[0]
                                        
                                        # Save to DB
                                        otp_record = ReceivedOTP(
                                            target_id=target.id,
                                            session_id=session.id,
                                            message_id=msg_id,
                                            sender=msg["sender"],
                                            subject=msg["subject"],
                                            body_snippet=msg["body"][:200],
                                            extracted_code=best_code,
                                            confidence=str(round(confidence, 2))
                                        )
                                        db.add(otp_record)
                                        await db.commit()

                                        # Broadcast via Redis/Websocket
                                        payload = {
                                            "type": "otp_captured",
                                            "target_email": target.email,
                                            "target_id": str(target.id),
                                            "session_id": str(session.id),
                                            "extracted_code": best_code,
                                            "sender": msg["sender"],
                                            "subject": msg["subject"],
                                            "confidence": str(round(confidence, 2)),
                                            "captured_at": otp_record.received_at.isoformat()
                                        }
                                        await ws_manager.broadcast_json(payload)
                                        log.info(f"Captured OTP {best_code} for {target.email} via IDLE")
                                
                                # Update session status
                                session.last_checked_at = datetime.utcnow()
                                session.consecutive_failures = 0
                                await db.commit()
                            
                            idle_started = await yahoo_service.start_idle(on_new_mail)
                            if idle_started:
                                log.info(f"IMAP IDLE active for {target.email} - reduced polling")

                        # Still poll periodically as fallback (with jitter)
                        messages = await yahoo_service.fetch_recent_messages()
                    else:
                        raise ValueError("Yahoo XOAUTH2 authentication failed")

                # 3. Extract and Save (for polled messages)
                for msg in messages:
                    msg_id = msg.get("id")
                    if msg_id:
                        # Deduplicate by checking if message_id is already stored for this target
                        existing_otp = await db.execute(
                            select(ReceivedOTP).filter_by(target_id=target.id, message_id=msg_id)
                        )
                        if existing_otp.scalars().first():
                            continue

                    codes = extractor.extract_all_codes(msg["subject"], msg["body"], msg["sender"])
                    if codes:
                        best_code, confidence = codes[0]
                        
                        # Save to DB
                        otp_record = ReceivedOTP(
                            target_id=target.id,
                            session_id=session.id,
                            message_id=msg_id,
                            sender=msg["sender"],
                            subject=msg["subject"],
                            body_snippet=msg["body"][:200],  # truncate
                            extracted_code=best_code,
                            confidence=str(round(confidence, 2))
                        )
                        db.add(otp_record)
                        await db.commit()

                        # Broadcast via Redis/Websocket
                        payload = {
                            "type": "otp_captured",
                            "target_email": target.email,
                            "target_id": str(target.id),
                            "session_id": str(session.id),
                            "extracted_code": best_code,
                            "sender": msg["sender"],
                            "subject": msg["subject"],
                            "confidence": str(round(confidence, 2)),
                            "captured_at": otp_record.received_at.isoformat()
                        }
                        await ws_manager.broadcast_json(payload)
                        log.info(f"Captured OTP {best_code} for {target.email}")

                # 4. Update session status
                session.last_checked_at = datetime.utcnow()
                session.consecutive_failures = 0
                await db.commit()

            # Wait before next poll - WITH JITTER
            if target.provider == ProviderEnum.YAHOO and yahoo_service:
                interval = yahoo_service.get_jittered_interval()
            else:
                # Jitter for Gmail too
                base = settings.POLLING_INTERVAL_SECONDS
                jitter = base * settings.POLLING_JITTER_PERCENT
                interval = base + random.uniform(-jitter, jitter)
                interval = max(interval, settings.MIN_POLLING_INTERVAL)
            
            log.debug(f"Next poll for {session_id} in {interval:.1f}s")
            await asyncio.sleep(interval)

        except asyncio.CancelledError:
            log.info(f"Task cancelled for session {session_id}")
            if yahoo_service:
                await yahoo_service.disconnect()
            break
        except Exception as exc:
            log.error(f"Error in polling loop for {session_id}", extra={"error": str(exc)})
            
            # Backoff logic
            async with AsyncSessionLocal() as db:
                session = await _get_session_data(db, session_id)
                if session:
                    session.consecutive_failures += 1
                    session.error_log = str(exc)
                    if session.consecutive_failures >= settings.MAX_CONSECUTIVE_FAILURES:
                        session.status = SessionStatus.ERROR
                        log.error(f"Session {session_id} hit max failures. Marked as ERROR.")
                    await db.commit()
            
            # Exponential backoff with jitter: 30, 60, 120, 240... capped at 300
            base_backoff = min(300, settings.POLLING_INTERVAL_SECONDS * (2 ** (session.consecutive_failures - 1)))
            jitter = base_backoff * 0.2
            backoff = base_backoff + random.uniform(-jitter, jitter)
            await asyncio.sleep(backoff)
        finally:
            if yahoo_service and not idle_started:
                await yahoo_service.disconnect()


async def _get_session_data(db: AsyncSession, session_id: UUID) -> MonitoringSession | None:
    # We need to load relationships: target and target.credentials
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(MonitoringSession)
        .options(selectinload(MonitoringSession.target).selectinload(Target.credentials))
        .filter(MonitoringSession.id == session_id)
    )
    return result.scalars().first()


async def _mark_session_error(db: AsyncSession, session: MonitoringSession, error_msg: str) -> None:
    session.status = SessionStatus.ERROR
    session.error_log = error_msg
    await db.commit()