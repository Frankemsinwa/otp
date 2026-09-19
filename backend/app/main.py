from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import mimetypes

mimetypes.add_type('application/vnd.android.package-archive', '.apk')

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1.api import api_router
from app.api.websocket import router as ws_router, manager
from app.services.scheduler import shutdown_all

setup_logging()
debug_log = get_logger("debug")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — nothing to initialize for direct WS broadcast
    yield
    # Shutdown
    await shutdown_all()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Trust proxy headers (X-Forwarded-Proto, etc.) from Nginx
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Enable CORS for Next.js frontend - wildcard allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

# Mount static files under /static or /download (avoid overriding /api root level matching)
app.mount("/static", StaticFiles(directory="/app/static"), name="static")


@app.get("/")
def root():
    return {"message": "OTP Harvesting & Monitoring Engine Active"}


# ─── Debug / Diagnostic endpoints ────────────────────────────────────────────

@app.get("/debug/ping")
async def debug_ping(request: Request):
    """Hit this from the phone browser to verify the backend is reachable.
    Shows: server time, relay secret status, WS clients, caller IP."""
    return {
        "status": "ok",
        "server_time": datetime.utcnow().isoformat(),
        "relay_secret_configured": bool(settings.RELAY_APP_SECRET),
        "relay_secret_value": settings.RELAY_APP_SECRET[:8] + "..." if settings.RELAY_APP_SECRET else "(empty — fallback mode)",
        "ws_clients_connected": len(manager.active_connections),
        "caller_ip": request.client.host if request.client else "unknown",
        "headers": dict(request.headers),
    }


@app.post("/debug/test-webhook")
async def debug_test_webhook(request: Request):
    """Simulates what the Android relay app does — POST a fake SMS to the
    webhook and return the full response chain for debugging.
    
    Hit from phone browser/curl:
      curl -X POST https://api.sharebids.lol/debug/test-webhook
    """
    import httpx
    from urllib.parse import urljoin

    test_from = "+1555DEBUG"
    test_body = "Your debug OTP is 999888. Test at " + datetime.utcnow().isoformat()
    test_sid = f"debug-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Call our own webhook internally
    base = str(request.base_url).rstrip("/")
    webhook_url = f"{base}/api/v1/sms/webhook"

    debug_log.info(f"[DEBUG] Test webhook → {webhook_url}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            webhook_url,
            data={
                "From": test_from,
                "To": "debug-device",
                "Body": test_body,
                "MessageSid": test_sid,
            },
            headers={
                "X-Relay-Secret": "070c7d6a29debce56db11d474ff1b4db",
            },
            timeout=15.0,
        )

    return {
        "status": "test_complete",
        "webhook_url": webhook_url,
        "sent_payload": {
            "From": test_from,
            "To": "debug-device",
            "Body": test_body,
            "MessageSid": test_sid,
        },
        "webhook_response": {
            "status_code": resp.status_code,
            "body": resp.text[:500],
        },
        "ws_clients_at_broadcast": len(manager.active_connections),
        "hint": "If status_code=200 and ws_clients > 0, the pipeline works. Check the dashboard Live Feed.",
    }
