"""
health.py — liveness endpoint.
GET /api/v1/health

Response 200:
  { "status": "ok", "env": "development", "version": "1.0.0" }
"""

from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()


@router.get(
    "/health",
    tags=["Health"],
    summary="Liveness check",
    responses={200: {"description": "API is up"}},
)
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": "1.0.0",
    }
