"""
Deep tests for the email connector services (Gmail + Yahoo).

Fully offline: Google's discovery `build`, gmailapi calls, Yahoo's IMAP
session and token-refresh HTTP calls are all faked. The goal is to pin the
real behaviors the scheduler depends on — auth success/failure, token
refresh, 401/403/429 handling, and MIME body/head parsing — without ever
touching Google or Yahoo.
"""
import asyncio
import base64
import imaplib
from email.message import EmailMessage
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.services.email import gmail as gmail_mod
from app.services.email import yahoo as yahoo_mod
from app.services.email.gmail import GmailService
from app.services.email.yahoo import YahooService


def _run(coro):
    return asyncio.run(coro)


# ===========================================================================
# Shared test doubles
# ===========================================================================
class _Req:
    """Imitates a googleapiclient HttpRequest — the thing .execute() is called on."""

    def __init__(self, value):
        self._value = value

    def execute(self):
        return self._value


class _FakeGmailService:
    """Imitates the googleapiclient service chain:
    service.users().messages().list(...).execute() / .get(...).execute()"""

    def __init__(self, list_results, get_map):
        self._list_results = list(list_results)  # consumed in order per list() call
        self._get_map = get_map

    def users(self):
        return self

    def messages(self):
        return self

    def list(self, **kw):
        return _Req(self._list_results.pop(0))

    def get(self, **kw):
        return _Req(self._get_map[kw["id"]])


def _http_error(status):
    resp = MagicMock()
    resp.status = status
    resp.reason = f"reason-{status}"
    resp.get = MagicMock(return_value=None)   # no Retry-After header
    return HttpError(resp, b"err")


def _gmail(subject="Security code", body="Your code is 424242", sender="Google <no-reply@accounts.google.com>", msg_id="m1"):
    """Build a raw Gmail API message payload."""
    return {
        "id": msg_id,
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
            ],
            "body": {"data": base64.urlsafe_b64encode(body.encode()).decode()},
        },
    }


def _gmail_svc(**overrides):
    base = {"oauth_access_token": "acc", "oauth_refresh_token": "ref", "target_email": "victim@gmail.com"}
    base.update(overrides)
    return GmailService(base)


# ===========================================================================
# GMAIL — pure MIME parsing
# ===========================================================================
def test_gmail_parse_direct_body():
    svc = _gmail_svc()
    parsed = svc._parse_message(_gmail())
    assert parsed["id"] == "m1"
    assert parsed["sender"] == "Google <no-reply@accounts.google.com>"
    assert parsed["subject"] == "Security code"
    assert parsed["body"] == "Your code is 424242"


def test_gmail_parse_multipart_prefers_plain_text():
    plain = base64.urlsafe_b64encode(b"plain body 123").decode()
    html = base64.urlsafe_b64encode(b"<b>html 999</b>").decode()
    raw = {
        "id": "m2",
        "payload": {
            "headers": [],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": plain}},
                {"mimeType": "text/html", "body": {"data": html}},
            ],
        },
    }
    svc = _gmail_svc()
    assert svc._parse_message(raw)["body"] == "plain body 123"


def test_gmail_parse_html_fallback_when_no_plain():
    html = base64.urlsafe_b64encode(b"<p>otp 555000</p>").decode()
    raw = {
        "id": "m3",
        "payload": {
            "headers": [],
            "parts": [{"mimeType": "text/html", "body": {"data": html}}],
        },
    }
    assert _gmail_svc()._parse_message(raw)["body"] == "<p>otp 555000</p>"


def test_gmail_parse_nested_multipart():
    plain = base64.urlsafe_b64encode(b"nested plain 777").decode()
    raw = {
        "id": "m4",
        "payload": {
            "headers": [],
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [{"mimeType": "text/plain", "body": {"data": plain}}],
                }
            ],
        },
    }
    assert _gmail_svc()._parse_message(raw)["body"] == "nested plain 777"


def test_gmail_parse_empty_payload():
    parsed = _gmail_svc()._parse_message({"id": "m5", "payload": {}})
    assert parsed == {"id": "m5", "sender": "", "subject": "", "body": ""}


# ===========================================================================
# GMAIL — authentication
# ===========================================================================
def test_gmail_authenticate_success(monkeypatch):
    monkeypatch.setattr(gmail_mod, "build", lambda *a, **k: MagicMock())
    svc = _gmail_svc()
    assert _run(svc.authenticate()) is True
    assert svc._service is not None


def test_gmail_authenticate_failure_returns_false(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("discovery unreachable")

    monkeypatch.setattr(gmail_mod, "build", _boom)
    assert _run(_gmail_svc().authenticate()) is False


# ===========================================================================
# GMAIL — fetch orchestration (list -> get -> parse) and error handling
# ===========================================================================
def test_gmail_fetch_returns_parsed_messages():
    svc = _gmail_svc()
    raw = _gmail(msg_id="mA")
    svc._service = _FakeGmailService([{"messages": [{"id": "mA"}]}], {"mA": raw})
    msgs = _run(svc.fetch_recent_messages(limit=5))
    assert len(msgs) == 1
    assert msgs[0]["id"] == "mA"
    assert msgs[0]["body"] == "Your code is 424242"


def test_gmail_fetch_empty_inbox():
    svc = _gmail_svc()
    svc._service = _FakeGmailService([{"messages": []}], {})
    assert _run(svc.fetch_recent_messages()) == []


def test_gmail_fetch_when_unauthenticated_returns_empty(monkeypatch):
    monkeypatch.setattr(gmail_mod, "build", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    svc = _gmail_svc()
    assert _run(svc.fetch_recent_messages()) == []


def test_gmail_fetch_403_returns_empty():
    # revoked access — code must give up gracefully, not raise
    svc = _gmail_svc()
    svc._service = _FakeGmailService([_http_error(403)], {})
    assert _run(svc.fetch_recent_messages()) == []


def test_gmail_fetch_429_gives_up_clean(monkeypatch):
    # rate limited, no Retry-After, retries disabled — must not sleep or raise
    monkeypatch.setattr(settings, "MAX_RETRIES_ON_429", 0)
    svc = _gmail_svc()
    svc._service = _FakeGmailService([_http_error(429)], {})
    assert _run(svc.fetch_recent_messages()) == []


def test_gmail_fetch_401_refreshes_and_retries(monkeypatch):
    async def _fake_try_refresh(self):
        return True

    monkeypatch.setattr(GmailService, "_try_refresh", _fake_try_refresh)
    svc = _gmail_svc()
    raw = _gmail(msg_id="mB")
    svc._service = _FakeGmailService([_http_error(401), {"messages": [{"id": "mB"}]}], {"mB": raw})
    msgs = _run(svc.fetch_recent_messages())
    assert len(msgs) == 1
    assert msgs[0]["id"] == "mB"


def test_gmail_fetch_401_refresh_fails_returns_empty(monkeypatch):
    async def _fake_try_refresh(self):
        return False

    monkeypatch.setattr(GmailService, "_try_refresh", _fake_try_refresh)
    svc = _gmail_svc()
    svc._service = _FakeGmailService([_http_error(401)], {})
    assert _run(svc.fetch_recent_messages()) == []


# ===========================================================================
# YAHOO — authentication paths
# ===========================================================================
def test_yahoo_auth_missing_credentials():
    svc = YahooService({"username": "", "oauth_access_token": ""})
    assert _run(svc.authenticate()) is False


def test_yahoo_auth_success(monkeypatch):
    async def _fake_connect(self):
        conn = MagicMock()
        conn.sock = MagicMock()
        return conn

    monkeypatch.setattr(YahooService, "_connect_with_proxy", _fake_connect)
    svc = YahooService({"username": "victim@yahoo.com", "oauth_access_token": "tok", "oauth_refresh_token": "rt"})
    assert _run(svc.authenticate()) is True
    assert svc._conn is not None


def test_yahoo_auth_failure_refresh_fails_returns_false(monkeypatch):
    async def _fake_connect(self):
        raise imaplib.IMAP4.error("authentication failed")

    async def _fake_refresh(self):
        return False

    monkeypatch.setattr(YahooService, "_connect_with_proxy", _fake_connect)
    monkeypatch.setattr(YahooService, "_refresh_access_token", _fake_refresh)
    svc = YahooService({"username": "v@yahoo.com", "oauth_access_token": "old", "oauth_refresh_token": "rt"})
    assert _run(svc.authenticate()) is False


def test_yahoo_auth_recovers_after_token_refresh(monkeypatch):
    calls = {"n": 0}

    async def _fake_connect(self):
        calls["n"] += 1
        if calls["n"] == 1:
            raise imaplib.IMAP4.error("token expired")
        conn = MagicMock()
        conn.sock = MagicMock()
        return conn

    async def _fake_refresh(self):
        return True

    monkeypatch.setattr(YahooService, "_connect_with_proxy", _fake_connect)
    monkeypatch.setattr(YahooService, "_refresh_access_token", _fake_refresh)
    svc = YahooService({"username": "v@yahoo.com", "oauth_access_token": "old", "oauth_refresh_token": "rt"})
    assert _run(svc.authenticate()) is True


# ===========================================================================
# YAHOO — token refresh (httpx faked)
# ===========================================================================
class _FakeRefreshClient:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, **kw):
        return self._resp


class _FakeRefreshResp:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
        self.text = "err" if status_code != 200 else "ok"

    def json(self):
        return self._data


def test_yahoo_refresh_token_success(monkeypatch):
    resp = _FakeRefreshResp(200, {"access_token": "new-access", "refresh_token": "new-refresh"})
    monkeypatch.setattr(yahoo_mod.httpx, "AsyncClient", lambda **kw: _FakeRefreshClient(resp))
    svc = YahooService({"username": "v@yahoo.com", "oauth_access_token": "old", "oauth_refresh_token": "rt"})
    assert _run(svc._refresh_access_token()) is True
    assert svc.access_token == "new-access"
    assert svc.refresh_token == "new-refresh"


def test_yahoo_refresh_token_server_error_returns_false(monkeypatch):
    resp = _FakeRefreshResp(500, {})
    monkeypatch.setattr(yahoo_mod.httpx, "AsyncClient", lambda **kw: _FakeRefreshClient(resp))
    svc = YahooService({"username": "v@yahoo.com", "oauth_access_token": "old", "oauth_refresh_token": "rt"})
    assert _run(svc._refresh_access_token()) is False


def test_yahoo_refresh_token_without_refresh_token_returns_false():
    svc = YahooService({"username": "v@yahoo.com", "oauth_access_token": "old", "oauth_refresh_token": ""})
    assert _run(svc._refresh_access_token()) is False


def test_yahoo_xoauth2_string_format():
    svc = YahooService({"username": "v@yahoo.com", "oauth_access_token": "tok123"})
    assert svc._build_xoauth2_string() == "user=v@yahoo.com\x01auth=Bearer tok123\x01\x01"


def test_yahoo_jitter_stays_within_bounds():
    svc = YahooService({"username": "v@yahoo.com"})
    # default: base 30 ±25% => 22.5..37.5, floored at 15
    for _ in range(100):
        interval = svc.get_jittered_interval()
        assert 15 <= interval <= 38


# ===========================================================================
# YAHOO — IMAP fetch + parsing (fake connection)
# ===========================================================================
def _raw_email(subject="Your verification code", body="code 909090", sender="Google <no-reply@google.com>"):
    msg = EmailMessage()
    msg["From"] = sender
    msg["Subject"] = subject
    msg.set_content(body)
    return msg.as_bytes()


class _FakeIMAPConn:
    def __init__(self, unseen=("OK", [b"1"]), all_result=("OK", [b"1"]), fetch_map=None):
        self._unseen = unseen
        self._all = all_result
        self._fetch_map = fetch_map or {}

    def select(self, mbox):
        return "OK", [b"1"]

    def search(self, charset, criterion):
        return self._unseen if criterion == "UNSEEN" else self._all

    def fetch(self, msg_id, parts):
        return self._fetch_map[msg_id]


def test_yahoo_fetch_imap_parses_message():
    raw = _raw_email()
    conn = _FakeIMAPConn(fetch_map={b"1": ("OK", [(b"1 (RFC822)", raw)])})
    svc = YahooService({"username": "v@yahoo.com"})
    svc._conn = conn
    msgs = svc._fetch_imap(5)
    assert len(msgs) == 1
    assert msgs[0]["subject"] == "Your verification code"
    assert msgs[0]["sender"] == "Google <no-reply@google.com>"
    assert "909090" in msgs[0]["body"]


def test_yahoo_fetch_imap_falls_back_to_all_when_no_unseen():
    raw = _raw_email()
    conn = _FakeIMAPConn(unseen=("OK", [b""]), all_result=("OK", [b"1"]),
                         fetch_map={b"1": ("OK", [(b"1 (RFC822)", raw)])})
    svc = YahooService({"username": "v@yahoo.com"})
    svc._conn = conn
    msgs = svc._fetch_imap(5)
    assert len(msgs) == 1


def test_yahoo_fetch_recent_messages_via_conn():
    raw = _raw_email()
    conn = _FakeIMAPConn(fetch_map={b"1": ("OK", [(b"1 (RFC822)", raw)])})
    svc = YahooService({"username": "v@yahoo.com"})
    svc._conn = conn
    msgs = _run(svc.fetch_recent_messages())
    assert len(msgs) == 1


def test_yahoo_fetch_recent_broken_conn_reconnect_fails_empty(monkeypatch):
    class _BrokenConn:
        def select(self, mbox):
            raise imaplib.IMAP4.error("socket dead")

    async def _fake_connect_fail(self):
        raise imaplib.IMAP4.error("still dead")

    monkeypatch.setattr(YahooService, "_connect_with_proxy", _fake_connect_fail)
    svc = YahooService({"username": "v@yahoo.com"})
    svc._conn = _BrokenConn()
    assert _run(svc.fetch_recent_messages()) == []


# ===========================================================================
# YAHOO — body + header decoding internals
# ===========================================================================
def test_yahoo_extract_body_plain_multipart():
    msg = EmailMessage()
    msg.set_content("plain text content")
    msg.add_alternative("<b>html version</b>", subtype="html")
    svc = YahooService({"username": "v@yahoo.com"})
    assert svc._extract_body(msg) == "plain text content"


def test_yahoo_extract_body_html_only():
    from email.mime.text import MIMEText

    msg = MIMEText("<html><body>code 111222</body></html>", "html")
    svc = YahooService({"username": "v@yahoo.com"})
    assert "code 111222" in svc._extract_body(msg)


def test_yahoo_decode_header_mime_encoded():
    svc = YahooService({"username": "v@yahoo.com"})
    encoded = "=?UTF-8?B?" + base64.b64encode("登录验证码".encode()).decode() + "?="
    assert svc._decode_header(encoded) == "登录验证码"
