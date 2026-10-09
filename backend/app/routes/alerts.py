"""
alerts.py — Capacity-risk alerts derived from forecast data in the DB.
All data comes from Supabase — no demo fallback.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.alert import AlertListResponse
from app.schemas.common import DataStatus
from app.services.alert_service import list_alerts

router = APIRouter()


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    tags=["Alerts"],
    summary="List active capacity-risk alerts",
    responses={503: {"description": "Database unavailable"}},
)
def list_alerts_route(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID, e.g. H001"),
):
    try:
        alerts, source = list_alerts(hospital_id=hospital_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"error": str(exc), "code": "DB_UNAVAILABLE"})
    return AlertListResponse(
        data=alerts,
        meta={"count": len(alerts), "page": 1, "page_size": len(alerts)},
        status=DataStatus.from_source(source),
    )
