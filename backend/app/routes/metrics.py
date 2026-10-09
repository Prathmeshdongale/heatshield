"""
metrics.py — ML model evaluation metrics endpoint.
Delegates entirely to metrics_service.
"""

from fastapi import APIRouter
from app.schemas.metrics import MetricsEnvelope, ModelMetrics
from app.schemas.common import DataStatus
from app.services.metrics_service import get_metrics

router = APIRouter()


@router.get(
    "/metrics",
    response_model=MetricsEnvelope,
    tags=["Metrics"],
    summary="Get latest ML model evaluation metrics",
)
def get_metrics_route():
    metrics, source = get_metrics()
    return MetricsEnvelope(
        data=ModelMetrics(**metrics),
        status=DataStatus.from_source(source),
    )
