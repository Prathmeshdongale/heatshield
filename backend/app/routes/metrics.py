"""
metrics.py — ML model evaluation metrics from the DB.
All data comes from Supabase — no demo fallback.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.metrics import MetricsEnvelope, ModelMetrics
from app.schemas.common import DataStatus
from app.services.metrics_service import get_metrics

router = APIRouter()


@router.get(
    "/metrics",
    response_model=MetricsEnvelope,
    tags=["Metrics"],
    summary="Get latest ML model evaluation metrics",
    responses={
        404: {"description": "No metrics in DB yet"},
        503: {"description": "Database unavailable"},
    },
)
def get_metrics_route():
    try:
        metrics, source = get_metrics()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": str(exc), "code": "NO_METRICS"})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"error": str(exc), "code": "DB_UNAVAILABLE"})
    return MetricsEnvelope(
        data=ModelMetrics(**metrics),
        status=DataStatus.from_source(source),
    )
