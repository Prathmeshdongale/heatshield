"""
metrics_repository.py — Supabase queries for the model_metrics table.

Returns the most-recent evaluation row (highest evaluated_on).
Falls back to DEMO_METRICS from mock_data.py if DB is unavailable.
"""

import logging
from app.integrations.supabase_client import get_supabase
from app.mock_data import DEMO_METRICS

logger = logging.getLogger(__name__)


def fetch_latest_metrics() -> dict | None:
    """
    Returns the latest model_metrics row, or None if the table is empty.
    Falls back to DEMO_METRICS on DB unavailability or error.
    """
    client = get_supabase()
    if client is None:
        return DEMO_METRICS

    try:
        resp = (
            client.table("model_metrics")
            .select(
                "model_version, evaluated_on, mae, rmse, r2, "
                "training_data_from, training_data_to, feature_count, data_status"
            )
            .order("evaluated_on", desc=True)
            .limit(1)
            .execute()
        )
        if not resp.data:
            logger.warning("model_metrics table is empty — returning demo metrics")
            return DEMO_METRICS
        return resp.data[0]

    except Exception as exc:
        logger.error("fetch_latest_metrics DB error: %s — falling back to demo", exc)
        return DEMO_METRICS


def save_metrics(metrics: dict) -> bool:
    """
    Upsert a new metrics row written by the ML pipeline.
    Returns True on success, False on failure.
    Expects keys matching the model_metrics table columns.
    """
    client = get_supabase()
    if client is None:
        logger.error("save_metrics: DB unavailable — metrics not persisted")
        return False

    try:
        client.table("model_metrics").upsert(metrics).execute()
        return True
    except Exception as exc:
        logger.error("save_metrics DB error: %s", exc)
        return False
