"""
Gmail email connector using Google Gmail API with OAuth 2.0.

Handles token refresh, message listing, MIME body parsing, and
graceful error handling for 401/403/429 responses.
"""
import asyncio
import base64
from typing import List, Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.email.base import BaseEmailService
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("services.gmail")


class GmailService(BaseEmailService):
    """
    Connects to a target's Gmail inbox via OAuth 2.0 tokens.

    credentials_data expects:
        - oauth_access_token: str (decrypted)
        - oauth_refresh_token: str (decrypted, optional but needed for refresh)
    """

    def __init__(self, credentials_data: Dict[str, Any]) -> None:
        super().__init__(credentials_data)
        self.access_token: str = credentials_data.get("oauth_access_token", "")
        self.refresh_token: str = credentials_data.get("oauth_refresh_token", "")
        self._service = None
        self._creds: Optional[Credentials] = None

    async def authenticate(self) -> bool:
        """Build Gmail API service using OAuth credentials. Refreshes if expired."""
        try:
            self._creds = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                scopes=settings.GMAIL_SCOPES,
            )

            # Refresh token if expired — run in thread since google-auth is sync
            if self._creds.expired and self._creds.refresh_token:
                await asyncio.to_thread(self._creds.refresh, GoogleAuthRequest())
                self.access_token = self._creds.token
                log.info("Gmail OAuth token refreshed")

            # Build the API service object (sync call, run in thread)
            self._service = await asyncio.to_thread(
                build, "gmail", "v1", credentials=self._creds
            )

            log.info("Gmail authentication successful")
            return True

        except Exception as exc:
            log.error("Gmail authentication failed", extra={"error": str(exc)})
            return False

    async def fetch_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent inbox messages via Gmail API."""
        if not self._service:
            authenticated = await self.authenticate()
            if not authenticated:
                log.warning("Cannot fetch messages — not authenticated")
                return []

        try:
            # List recent message IDs
            result = await asyncio.to_thread(
                lambda: self._service.users()
                .messages()
                .list(userId="me", maxResults=limit, q="is:inbox")
                .execute()
            )

            messages_meta = result.get("messages", [])
            if not messages_meta:
                return []

            # Fetch full message content for each ID
            parsed_messages = []
            for msg_meta in messages_meta:
                msg_data = await self._fetch_message(msg_meta["id"])
                if msg_data:
                    parsed_messages.append(msg_data)

            log.info(f"Fetched {len(parsed_messages)} messages from Gmail")
            return parsed_messages

        except HttpError as exc:
            status = exc.resp.status if exc.resp else 0
            if status == 401:
                log.warning("Gmail 401 — token expired, attempting refresh")
                if await self._try_refresh():
                    return await self.fetch_recent_messages(limit)
            elif status == 429:
                log.warning("Gmail 429 — rate limited, backing off")
            elif status == 403:
                log.error("Gmail 403 — access revoked or insufficient scopes")
            else:
                log.error(f"Gmail API error {status}", extra={"error": str(exc)})
            return []

        except Exception as exc:
            log.error("Gmail fetch failed", extra={"error": str(exc)})
            return []

    async def disconnect(self) -> None:
        """No persistent connection to close for REST API."""
        self._service = None
        self._creds = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _fetch_message(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse a single Gmail message by ID."""
        try:
            raw = await asyncio.to_thread(
                lambda: self._service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            return self._parse_message(raw)
        except Exception as exc:
            log.warning(f"Failed to fetch message {msg_id}", extra={"error": str(exc)})
            return None

    def _parse_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sender, subject, and decoded body from Gmail API message format."""
        headers = {h["name"].lower(): h["value"] for h in raw_msg.get("payload", {}).get("headers", [])}

        sender = headers.get("from", "")
        subject = headers.get("subject", "")
        body = self._extract_body(raw_msg.get("payload", {}))

        return {
            "id": raw_msg.get("id", ""),
            "sender": sender,
            "subject": subject,
            "body": body,
        }

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Recursively extract text body from MIME payload."""
        # Direct body data
        body_data = payload.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

        # Multipart — walk parts looking for text/plain then text/html
        parts = payload.get("parts", [])
        text_body = ""
        html_body = ""

        for part in parts:
            mime = part.get("mimeType", "")
            part_data = part.get("body", {}).get("data")

            if part_data:
                decoded = base64.urlsafe_b64decode(part_data).decode("utf-8", errors="replace")
                if mime == "text/plain":
                    text_body = decoded
                elif mime == "text/html":
                    html_body = decoded

            # Recurse into nested multipart
            if part.get("parts"):
                nested = self._extract_body(part)
                if nested:
                    text_body = text_body or nested

        return text_body or html_body

    async def _try_refresh(self) -> bool:
        """Attempt to refresh the access token."""
        if not self._creds or not self._creds.refresh_token:
            return False
        try:
            await asyncio.to_thread(self._creds.refresh, GoogleAuthRequest())
            self.access_token = self._creds.token
            self._service = await asyncio.to_thread(
                build, "gmail", "v1", credentials=self._creds
            )
            log.info("Gmail token refresh successful")
            return True
        except Exception as exc:
            log.error("Gmail token refresh failed", extra={"error": str(exc)})
            return False

    def get_refreshed_token(self) -> Optional[str]:
        """Return the current access token (may have been refreshed)."""
        return self._creds.token if self._creds else None
