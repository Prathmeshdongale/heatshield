"""
router.py — mounts every sub-router under the versioned /api/v1 prefix.
Add new route modules here as they are implemented.
"""

from fastapi import APIRouter
from app.routes import health, hospitals, weather, forecasts, alerts, metrics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(hospitals.router)
api_router.include_router(weather.router)
api_router.include_router(forecasts.router)
api_router.include_router(alerts.router)
api_router.include_router(metrics.router)
