"""
weather.py — Weather observations endpoint.
All data comes from Supabase — no demo fallback.
"""

from fastapi import APIRouter, HTTPException, Query
from app.schemas.weather import WeatherEnvelope, WeatherResponse
from app.schemas.common import DataStatus
from app.services.weather_service import get_weather

router = APIRouter()


@router.get(
    "/weather",
    response_model=WeatherEnvelope,
    tags=["Weather"],
    summary="Get weather observations for a hospital region",
    responses={
        422: {"description": "Invalid query parameters"},
        503: {"description": "Database unavailable"},
    },
)
def get_weather_route(
    hospital_id: str = Query(..., description="Hospital ID, e.g. H001"),
    days: int = Query(7, ge=1, le=14, description="Number of past days to return (1–14)"),
):
    try:
        weather, source = get_weather(hospital_id, days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"error": str(exc), "code": "DB_UNAVAILABLE"})
    return WeatherEnvelope(
        data=WeatherResponse(**weather),
        status=DataStatus.from_source(source),
    )
