"""
Signal — API v1 Master Router
Combines all v1 sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.ask import router as ask_router
from app.api.v1.auth import router as auth_router
from app.api.v1.behavior import router as behavior_router
from app.api.v1.focus import router as focus_router
from app.api.v1.overview import router as overview_router
from app.api.v1.signals import router as signals_router
from app.api.v1.timeline import router as timeline_router
from app.api.v1.webhooks import router as webhooks_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(overview_router)
api_v1_router.include_router(focus_router)
api_v1_router.include_router(timeline_router)
api_v1_router.include_router(behavior_router)
api_v1_router.include_router(ask_router)
api_v1_router.include_router(signals_router)
api_v1_router.include_router(webhooks_router)
