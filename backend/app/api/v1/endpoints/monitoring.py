from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db
from app.models.session import MonitoringSession, SessionStatus
from app.models.target import Target
from app.models.otp import ReceivedOTP
from app.schemas.session import SessionResponse
from app.schemas.otp import OTPResponse
from app.core.logging import get_logger

from app.services.scheduler import stop_polling_task, start_polling_task

log = get_logger("api.monitoring")
router = APIRouter()


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(status_filter: SessionStatus = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List monitoring sessions, optionally filtered by status."""
    query = select(MonitoringSession).offset(skip).limit(limit)
    if status_filter:
        query = query.filter(MonitoringSession.status == status_filter)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get details of a specific monitoring session."""
    result = await db.execute(select(MonitoringSession).filter(MonitoringSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/otps", response_model=List[OTPResponse])
async def get_session_otps(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get OTP history for a specific monitoring session."""
    result = await db.execute(
        select(ReceivedOTP)
        .filter(ReceivedOTP.session_id == session_id)
        .order_by(ReceivedOTP.received_at.desc())
    )
    return result.scalars().all()


@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Stop an active polling session."""
    result = await db.execute(select(MonitoringSession).filter(MonitoringSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = SessionStatus.STOPPED
    await db.commit()
    
    await stop_polling_task(session_id)
    log.info(f"Session {session_id} manually stopped.")
    return {"status": "stopped", "session_id": str(session_id)}


@router.post("/sessions/{session_id}/restart")
async def restart_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Restart a stopped or errored polling session."""
    result = await db.execute(select(MonitoringSession).filter(MonitoringSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = SessionStatus.POLLING
    session.consecutive_failures = 0
    await db.commit()
    
    await start_polling_task(session_id)
    log.info(f"Session {session_id} manually restarted.")
    return {"status": "restarted", "session_id": str(session_id)}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate monitoring statistics."""
    # Total targets
    total_targets_res = await db.execute(select(func.count(Target.id)))
    total_targets = total_targets_res.scalar()

    # Active sessions
    active_sessions_res = await db.execute(
        select(func.count(MonitoringSession.id)).filter(MonitoringSession.status == SessionStatus.POLLING)
    )
    active_sessions = active_sessions_res.scalar()

    # OTPs captured today (last 24h for simplicity here)
    # Use timezone-naive UTC to match SQLAlchemy asyncpg defaults
    yesterday = datetime.utcnow() - timedelta(days=1)
    otps_today_res = await db.execute(
        select(func.count(ReceivedOTP.id)).filter(ReceivedOTP.received_at >= yesterday)
    )
    otps_today = otps_today_res.scalar()

    return {
        "total_targets": total_targets,
        "active_sessions": active_sessions,
        "otps_captured_24h": otps_today
    }
