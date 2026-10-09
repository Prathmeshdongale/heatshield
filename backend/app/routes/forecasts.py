"""
forecasts.py — Demand forecast endpoint.
All data comes from Supabase — no demo fallback.
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
        503: {"description": "ML model unavailable or DB unreachable"},
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
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": str(exc), "code": "DB_UNAVAILABLE"},
        )
    return ForecastEnvelope(
        data=ForecastResponse(**forecast),
        status=DataStatus.from_source(source),
    )
