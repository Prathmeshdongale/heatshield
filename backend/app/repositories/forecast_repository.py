"""
forecast_repository.py — Supabase queries for forecasts table.
No demo fallback — returns real DB data or raises on failure.
"""

import logging
from datetime import date, timedelta
from app.integrations.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def fetch_forecast(hospital_id: str, days: int) -> dict:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client not configured")

    hid = hospital_id.upper()
    today     = date.today()
    date_from = str(today + timedelta(days=1))
    date_to   = str(today + timedelta(days=days))

    rows = client.select(
        "forecasts",
        columns="forecast_date,predicted_admissions,confidence_lower,confidence_upper,risk_status,model_version,generated_at",
        filters={"hospital_id": hid},
        order="forecast_date",
    )

    # Filter to date range in Python (PostgREST eq only does equality)
    rows = [r for r in rows if date_from <= r["forecast_date"] <= date_to]

    # Deduplicate — keep latest generated_at per forecast_date
    seen: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: r.get("generated_at", ""), reverse=True):
        fd = row["forecast_date"]
        if fd not in seen:
            seen[fd] = row

    points = sorted(seen.values(), key=lambda r: r["forecast_date"])

    model_version = points[0]["model_version"] if points else "unknown"
    generated_at  = points[0]["generated_at"]  if points else date.today().isoformat()

    return {
        "hospital_id":    hid,
        "model_version":  model_version,
        "generated_at":   generated_at,
        "days_requested": days,
        "points": [
            {
                "forecast_date":        p["forecast_date"],
                "predicted_admissions": float(p["predicted_admissions"]),
                "confidence_lower":     float(p["confidence_lower"]),
                "confidence_upper":     float(p["confidence_upper"]),
                "risk_status":          p["risk_status"],
            }
            for p in points
        ],
    }


def save_forecast_points(hospital_id: str, points: list[dict], model_version: str) -> bool:
    client = get_supabase()
    if client is None:
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
    return client.insert("forecasts", rows)
