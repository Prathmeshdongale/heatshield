"""
forecasts.py — Demand forecast endpoint.
Delegates entirely to forecast_service.

503 is returned when the ML model is unavailable in live mode.
The route never substitutes fabricated data on model failure.
"""

from fastapi import APIRouter, HTTPException, Query
from app.schemas.forecast import ForecastEnvelope, ForecastResponse
from app.schemas.common import DataStatus
from app.services.forecast_service import (
    get_forecast,
    HospitalNotFoundError,
    ForecastUnavailableError,
)

router = APIRouter()


@router.get(
    "/forecasts",
    response_model=ForecastEnvelope,
    tags=["Forecasts"],
    summary="Get demand forecast for a hospital",
    responses={
        404: {"description": "Hospital not found"},
        422: {"description": "Invalid query parameters"},
        503: {"description": "ML model unavailable"},
    },
)
def get_forecast_route(
    hospital_id: str = Query(..., description="Hospital ID, e.g. H001"),
    days: int = Query(7, ge=1, le=14, description="Forecast horizon in days (1–14)"),
):
    try:
        forecast, source = get_forecast(hospital_id, days)
    except HospitalNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Hospital '{hospital_id}' not found", "code": "HOSPITAL_NOT_FOUND"},
        )
    except ForecastUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": str(exc), "code": "FORECAST_UNAVAILABLE"},
        )

    return ForecastEnvelope(
        data=ForecastResponse(**forecast),
        status=DataStatus.from_source(source),
    )
