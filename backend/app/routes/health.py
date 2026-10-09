"""
health.py — liveness endpoint.
GET /api/v1/health

Response 200:
  { "status": "ok", "env": "development", "version": "1.0.0",
    "demo_mode": true, "db_connected": false }
"""

from fastapi import APIRouter
from app.config import get_settings
from app.integrations.supabase_client import is_db_available

router = APIRouter()


@router.get(
    "/health",
    tags=["Health"],
    summary="Liveness check — also reports demo mode and DB connectivity",
    responses={200: {"description": "API is up"}},
)
def health_check():
    settings = get_settings()
    db_connected = is_db_available() if not settings.demo_mode else False
    return {
        "status":       "ok",
        "env":          settings.app_env,
        "version":      "1.0.0",
        "demo_mode":    settings.demo_mode,
        "db_connected": db_connected,
    }
