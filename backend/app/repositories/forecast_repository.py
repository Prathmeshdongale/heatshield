"""
forecast_repository.py — Supabase queries for the forecasts table.

For each (hospital_id, forecast_date) the query returns the row with the
latest generated_at, so callers always get the most-recent model run.

Falls back to mock_data.get_demo_forecast() if DB is unavailable.
"""

import logging
from datetime import date, timedelta
from typing import Any
from app.integrations.supabase_client import get_supabase
from app.mock_data import get_demo_forecast

logger = logging.getLogger(__name__)


def fetch_forecast(hospital_id: str, days: int) -> dict:
    """
    Returns forecast points for the next `days` calendar days.
    One point per day, using the most-recently generated row per date.
    Falls back to demo data on error.
    """
    client = get_supabase()
    hid = hospital_id.upper()

    if client is None:
        return get_demo_forecast(hid, days)

    today = date.today()
    date_from = str(today + timedelta(days=1))
    date_to = str(today + timedelta(days=days))

    try:
        resp = (
            client.table("forecasts")
            .select(
                "forecast_date, predicted_admissions, confidence_lower, "
                "confidence_upper, risk_status, model_version, generated_at"
            )
            .eq("hospital_id", hid)                   # parameterised
            .gte("forecast_date", date_from)           # parameterised
            .lte("forecast_date", date_to)             # parameterised
            .order("forecast_date", desc=False)
            .order("generated_at", desc=True)
            .execute()
        )

        # Deduplicate: keep latest generated_at per forecast_date
        seen: dict[str, dict] = {}
        for row in resp.data:
            fd = row["forecast_date"]
            if fd not in seen:
                seen[fd] = row

        points = sorted(seen.values(), key=lambda r: r["forecast_date"])

        # Extract model_version from the first point (all should be the same run)
        model_version = points[0]["model_version"] if points else "unknown"
        generated_at = points[0]["generated_at"] if points else ""

        return {
            "hospital_id": hid,
            "model_version": model_version,
            "generated_at": generated_at,
            "days_requested": days,
            "points": [
                {
                    "forecast_date": p["forecast_date"],
                    "predicted_admissions": float(p["predicted_admissions"]),
                    "confidence_lower": float(p["confidence_lower"]),
                    "confidence_upper": float(p["confidence_upper"]),
                    "risk_status": p["risk_status"],
                }
                for p in points
            ],
        }

    except Exception as exc:
        logger.error("fetch_forecast DB error (%s): %s — falling back to demo", hid, exc)
        return get_demo_forecast(hid, days)


def save_forecast_points(hospital_id: str, points: list[dict], model_version: str) -> bool:
    """
    Persist ML-generated forecast points to the forecasts table.
    Each dict in `points` must match the forecasts table schema.
    Returns True on success, False on failure (caller decides how to handle).
    """
    client = get_supabase()
    if client is None:
        logger.error("save_forecast_points: DB unavailable — forecasts not persisted")
        return False

    rows = [
        {
            "hospital_id":           hospital_id.upper(),
            "forecast_date":         p["forecast_date"],
            "model_version":         model_version,
            "predicted_admissions":  p["predicted_admissions"],
            "confidence_lower":      p["confidence_lower"],
            "confidence_upper":      p["confidence_upper"],
            "risk_status":           p["risk_status"],
            "data_status":           "live",
        }
        for p in points
    ]

    try:
        client.table("forecasts").insert(rows).execute()
        return True
    except Exception as exc:
        logger.error("save_forecast_points DB error (%s): %s", hospital_id, exc)
        return False
