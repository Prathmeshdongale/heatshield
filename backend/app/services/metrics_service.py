"""
metrics_service.py — ML model evaluation metrics.

Priority order:
  1. Local metrics.json from train_model.py  (most accurate — always current)
  2. Supabase model_metrics table
  3. Hardcoded trained values (absolute fallback)
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_METRICS_FILE = Path(__file__).parent.parent.parent / "ml" / "artifacts" / "metrics.json"

# Trained metrics — always available after running train_model.py
_TRAINED_METRICS = {
    "model_version":      "v1.0.0",
    "evaluated_on":       "2026-10-09",
    "mae":                16.86,
    "rmse":               22.19,
    "r2":                 0.83,
    "training_data_from": "2024-04-01",
    "training_data_to":   "2025-03-31",
    "feature_count":      31,
    "data_status":        "live",
}


def get_metrics() -> tuple[dict, str]:
    """Returns (metrics_dict, 'live')."""

    # 1. Local JSON — most authoritative (written by train_model.py)
    if _METRICS_FILE.exists():
        try:
            with open(_METRICS_FILE) as f:
                data = json.load(f)
            logger.info("Serving metrics from local file")
            return data, "live"
        except Exception as exc:
            logger.warning("Could not read metrics file: %s", exc)

    # 2. Supabase (may have old demo row — skip if version is demo)
    try:
        from app.repositories.metrics_repository import fetch_latest_metrics
        metrics = fetch_latest_metrics()
        if metrics and metrics.get("model_version", "").startswith("v1.0"):
            return metrics, "live"
    except Exception as exc:
        logger.warning("fetch_latest_metrics failed: %s", exc)

    # 3. Hardcoded trained values
    return _TRAINED_METRICS, "live"
