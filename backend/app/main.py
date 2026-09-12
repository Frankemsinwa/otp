from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.api.websocket import router as ws_router
from app.api.websocket import manager as ws_manager
from app.services.scheduler import shutdown_all

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ws_manager.connect_redis()
    yield
    # Shutdown
    await shutdown_all()
    await ws_manager.disconnect_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

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
app.mount("/static", StaticFiles(directory="/app"), name="static")


@app.get("/")
def root():
    return {"message": "OTP Harvesting & Monitoring Engine Active"}
