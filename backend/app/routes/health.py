"""
health.py — Liveness endpoint.
GET /api/v1/health → { status, env, version, demo_mode, db_connected, model_loaded, model_version }
"""

from fastapi import APIRouter
from app.config import get_settings
from app.integrations.supabase_client import is_db_available
from app.integrations.ml_adapter import is_model_loaded, get_model_version

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Liveness check")
def health_check():
    settings = get_settings()
    db_connected  = is_db_available() if not settings.demo_mode else False
    model_ready   = is_model_loaded()
    return {
        "status":        "ok",
        "env":           settings.app_env,
        "version":       "1.0.0",
        "demo_mode":     settings.demo_mode,
        "db_connected":  db_connected,
        "model_loaded":  model_ready,
        "model_version": get_model_version() if model_ready else None,
    }
