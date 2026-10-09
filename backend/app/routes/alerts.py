"""
alerts.py — Capacity-risk alerts endpoint.
Delegates entirely to alert_service.
Alerts are derived from forecast data — no separate alerts table yet.
"""

from fastapi import APIRouter, Query
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
)
def list_alerts_route(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID, e.g. H001"),
):
    alerts, source = list_alerts(hospital_id=hospital_id)
    return AlertListResponse(
        data=alerts,
        meta={"count": len(alerts), "page": 1, "page_size": len(alerts)},
        status=DataStatus.from_source(source),
    )
