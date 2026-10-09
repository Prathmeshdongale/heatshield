"""
metrics_repository.py — Supabase queries for model_metrics table.
No demo fallback — returns real DB data or raises on failure.
"""

import logging
from app.integrations.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def fetch_latest_metrics() -> dict | None:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client not configured")

    rows = client.select(
        "model_metrics",
        columns="model_version,evaluated_on,mae,rmse,r2,training_data_from,training_data_to,feature_count,data_status",
        order="evaluated_on",
        desc=True,
        limit=1,
    )
    return rows[0] if rows else None


def save_metrics(metrics: dict) -> bool:
    client = get_supabase()
    if client is None:
        return False
    return client.insert("model_metrics", [metrics], upsert=True)
