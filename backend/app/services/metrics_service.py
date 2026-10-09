"""
metrics_service.py — ML model evaluation metrics from the real database.
No demo fallback — all data comes from Supabase.
"""

import logging
from app.repositories.metrics_repository import fetch_latest_metrics

logger = logging.getLogger(__name__)


def get_metrics() -> tuple[dict, str]:
    """
    Returns (metrics_dict, 'live').
    Raises RuntimeError if DB is unreachable.
    Raises ValueError if no metrics rows exist.
    """
    metrics = fetch_latest_metrics()
    if metrics is None:
        raise ValueError("No model metrics found in the database.")
    return metrics, "live"
