from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json
import urllib.parse
import random
import hashlib
import httpx

from app.api.deps import get_db
from app.core.config import settings
from app.models.target import Target, ProviderEnum, TargetStatus
from app.models.credential import Credential
from app.models.session import MonitoringSession, SessionStatus
from app.core.security import encrypt_token
from app.core.logging import get_logger

from app.services.scheduler import start_polling_task

log = get_logger("api.oauth")
router = APIRouter()


def _select_gmail_client(target_email: str) -> tuple[str, str]:
    """Select Gmail OAuth client from pool deterministically."""
    client_id = settings.GMAIL_CLIENT_ID
    client_secret = settings.GMAIL_CLIENT_SECRET
    
    if settings.GMAIL_CLIENT_POOL:
        try:
            pool = [p.strip() for p in settings.GMAIL_CLIENT_POOL.split(",") if p.strip()]
            if pool:
                idx = int(hashlib.md5(target_email.encode()).hexdigest(), 16) % len(pool)
                client_pair = pool[idx].split(":")
                if len(client_pair) == 2:
                    client_id, client_secret = client_pair
        except Exception as exc:
            log.warning(f"Failed to parse GMAIL_CLIENT_POOL: {exc}")
    
    return client_id, client_secret


def _select_yahoo_client(target_email: str) -> tuple[str, str]:
    """Select Yahoo OAuth client from pool deterministically."""
    client_id = settings.YAHOO_CLIENT_ID
    client_secret = settings.YAHOO_CLIENT_SECRET
    
    if settings.YAHOO_CLIENT_POOL:
        try:
            pool = [p.strip() for p in settings.YAHOO_CLIENT_POOL.split(",") if p.strip()]
            if pool:
                idx = int(hashlib.md5(target_email.encode()).hexdigest(), 16) % len(pool)
                client_pair = pool[idx].split(":")
                if len(client_pair) == 2:
                    client_id, client_secret = client_pair
        except Exception as exc:
            log.warning(f"Failed to parse YAHOO_CLIENT_POOL: {exc}")
    
    return client_id, client_secret


@router.get("/gmail/authorize")
async def authorize_gmail(target_email: str):
    """
    Generate Google OAuth consent URL.
    The frontend can redirect the user here, passing the target's email.
    We embed the target_email in the 'state' parameter to recover it in the callback.
    """
    client_id, _ = _select_gmail_client(target_email)
    
    if not client_id:
        raise HTTPException(status_code=500, detail="GMAIL_CLIENT_ID not configured")

    state = urllib.parse.quote(target_email)
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(settings.GMAIL_REDIRECT_URI)}&"
        "response_type=code&"
        f"scope={urllib.parse.quote(' '.join(settings.GMAIL_SCOPES))}&"
        "access_type=offline&"
        "prompt=consent&"
        f"state={state}"
    )
    
    # Use RedirectResponse to actually redirect the user's browser
    return RedirectResponse(url=auth_url)


@router.get("/gmail/callback")
async def gmail_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """
    Handle OAuth redirect, exchange code for tokens, store encrypted tokens against target.
    """
    target_email = urllib.parse.unquote(state)
    
    # Select the same client that was used for authorization
    client_id, client_secret = _select_gmail_client(target_email)
    
    # 1. Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": settings.GMAIL_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=payload)
        
    if resp.status_code != 200:
        log.error("Failed to exchange OAuth code", extra={"response": resp.text})
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token returned")

    # 2. Get or create Target
    result = await db.execute(select(Target).filter(Target.email == target_email))
    target = result.scalars().first()
    if not target:
        target = Target(email=target_email, provider=ProviderEnum.GMAIL, status=TargetStatus.ACTIVE)
        db.add(target)
        await db.flush()
    else:
        target.status = TargetStatus.ACTIVE
        target.provider = ProviderEnum.GMAIL

    # 3. Create or update Credential
    cred_res = await db.execute(select(Credential).filter(Credential.target_id == target.id))
    credential = cred_res.scalars().first()
    
    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token) if refresh_token else None

    if not credential:
        credential = Credential(
            target_id=target.id,
            username=target_email,
            oauth_access_token=enc_access,
            oauth_refresh_token=enc_refresh
        )
        db.add(credential)
    else:
        credential.oauth_access_token = enc_access
        if enc_refresh:
            credential.oauth_refresh_token = enc_refresh

    # 4. Create Monitoring Session
    session = MonitoringSession(target_id=target.id, status=SessionStatus.POLLING)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    log.info(f"OAuth flow completed for {target_email}. Tokens encrypted and stored.")
    
    # 5. Dispatch to background scheduler
    await start_polling_task(session.id)

    # Redirect back to dashboard so user sees the active session
    return RedirectResponse(url="http://localhost:3000/dashboard?oauth_success=true")


# ============================================================================
# Yahoo OAuth 2.0
# ============================================================================

@router.get("/yahoo/authorize")
async def authorize_yahoo(target_email: str):
    """
    Generate Yahoo OAuth consent URL and redirect the user there.
    """
    client_id, _ = _select_yahoo_client(target_email)
    
    if not client_id:
        raise HTTPException(status_code=500, detail="YAHOO_CLIENT_ID not configured")

    state = urllib.parse.quote(target_email)

    auth_url = (
        "https://api.login.yahoo.com/oauth2/request_auth?"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(settings.YAHOO_REDIRECT_URI)}&"
        "response_type=code&"
        "language=en-us&"
        f"state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/yahoo/callback")
async def yahoo_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """
    Handle Yahoo OAuth redirect — exchange code for tokens, store encrypted, start monitoring.
    """
    target_email = urllib.parse.unquote(state)

    # Select the same client that was used for authorization
    client_id, client_secret = _select_yahoo_client(target_email)

    # 1. Exchange code for tokens
    token_url = "https://api.login.yahoo.com/oauth2/get_token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": settings.YAHOO_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(client_id, client_secret),
        )

    if resp.status_code != 200:
        log.error("Failed to exchange Yahoo OAuth code", extra={"response": resp.text})
        raise HTTPException(status_code=400, detail="Failed to exchange Yahoo authorization code")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token returned from Yahoo")

    # 2. Get email from Yahoo userinfo (xoauth_yahoo_guid is in the token response)
    yahoo_guid = token_data.get("xoauth_yahoo_guid", "")

    # 3. Get or create Target
    result = await db.execute(select(Target).filter(Target.email == target_email))
    target = result.scalars().first()
    if not target:
        target = Target(email=target_email, provider=ProviderEnum.YAHOO, status=TargetStatus.ACTIVE)
        db.add(target)
        await db.flush()
    else:
        target.status = TargetStatus.ACTIVE
        target.provider = ProviderEnum.YAHOO

    # 4. Create or update Credential with OAuth tokens
    cred_res = await db.execute(select(Credential).filter(Credential.target_id == target.id))
    credential = cred_res.scalars().first()

    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token) if refresh_token else None

    if not credential:
        credential = Credential(
            target_id=target.id,
            username=target_email,
            oauth_access_token=enc_access,
            oauth_refresh_token=enc_refresh
        )
        db.add(credential)
    else:
        credential.oauth_access_token = enc_access
        if enc_refresh:
            credential.oauth_refresh_token = enc_refresh

    # 5. Create Monitoring Session
    session = MonitoringSession(target_id=target.id, status=SessionStatus.POLLING)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    log.info(f"Yahoo OAuth flow completed for {target_email}. Tokens encrypted and stored.")

    # 6. Dispatch to background scheduler
    await start_polling_task(session.id)

    return RedirectResponse(url="http://localhost:3000/dashboard?oauth_success=true")