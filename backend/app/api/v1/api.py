from fastapi import APIRouter
from app.api.v1.endpoints import targets, harvest, monitoring, oauth, sms

api_router = APIRouter()

api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(harvest.router, prefix="/harvest", tags=["harvest"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
api_router.include_router(sms.router, prefix="/sms", tags=["sms"])
