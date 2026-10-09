"""
metrics_service.py — retrieves the latest ML model evaluation metrics.

In demo mode: returns DEMO_METRICS from mock_data.py.
In live mode: reads the most-recent row from the model_metrics table.
              Falls back to DEMO_METRICS with a warning if the table is empty.
"""

import logging
from app.config import get_settings
from app.repositories.metrics_repository import fetch_latest_metrics
from app.mock_data import DEMO_METRICS

logger = logging.getLogger(__name__)


def get_metrics() -> tuple[dict, str]:
    """
    Returns (metrics_dict, data_source).
    data_source: 'demo' | 'live'
    """
    settings = get_settings()

    if settings.demo_mode:
        return DEMO_METRICS, "demo"

    metrics = fetch_latest_metrics()
    if metrics is None or metrics == DEMO_METRICS:
        logger.warning("No live metrics found — returning demo metrics")
        return DEMO_METRICS, "demo"

    return metrics, "live"
