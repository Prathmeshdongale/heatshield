"""
weather.py — Weather observations endpoint.
Delegates entirely to weather_service.
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
        404: {"description": "Hospital not found"},
        422: {"description": "Invalid query parameters"},
    },
)
def get_weather_route(
    hospital_id: str = Query(..., description="Hospital ID, e.g. H001"),
    days: int = Query(7, ge=1, le=14, description="Number of past days to return (1–14)"),
):
    try:
        weather, source = get_weather(hospital_id, days)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Hospital '{hospital_id}' not found", "code": "HOSPITAL_NOT_FOUND"},
        )
    return WeatherEnvelope(
        data=WeatherResponse(**weather),
        status=DataStatus.from_source(source),
    )
