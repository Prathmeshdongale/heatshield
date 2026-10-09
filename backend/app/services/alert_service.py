"""
alert_service.py — derives capacity-risk alerts from forecast data.

Alerts are NOT stored in their own table at this stage; they are computed
on-the-fly from the forecasts table (or demo forecast data).
A future step can add an `alerts` table and a background job.

Alert generation rules (agreed with frontend — do not change field names):
  Any forecast point whose risk_status is 'red' or 'critical' generates
  an alert. Severity maps as:
      red      → high
      critical → critical

Alerts are deduplicated per (hospital_id, forecast_date) — one alert per
day per hospital.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.repositories.forecast_repository import fetch_forecast
from app.repositories.hospital_repository import fetch_all_hospitals, fetch_hospital_by_id
from app.mock_data import get_demo_alerts, HOSPITALS

logger = logging.getLogger(__name__)

_ALERT_RISK_LEVELS = {"red", "critical"}
_RISK_TO_SEVERITY  = {"red": "high", "critical": "critical"}


def _alerts_from_forecast(hospital: dict, forecast: dict) -> list[dict]:
    """Derive alert dicts from a forecast response dict."""
    alerts = []
    for point in forecast.get("points", []):
        risk = point.get("risk_status", "")
        if risk not in _ALERT_RISK_LEVELS:
            continue
        alerts.append({
            "alert_id":     f"ALT-{hospital['hospital_id']}-{point['forecast_date']}",
            "hospital_id":  hospital["hospital_id"],
            "hospital_name": hospital.get("name", hospital["hospital_id"]),
            "severity":     _RISK_TO_SEVERITY[risk],
            "message": (
                f"Predicted admissions ({point['predicted_admissions']:.1f}) "
                f"indicate {risk} capacity risk on {point['forecast_date']}"
            ),
            "triggered_at":  datetime.now(timezone.utc),
            "forecast_date": point["forecast_date"],
            "resolved":      False,
        })
    return alerts


def list_alerts(hospital_id: Optional[str] = None) -> tuple[list[dict], str]:
    """
    Returns (alerts, data_source).
    Filters to one hospital when hospital_id is provided.
    Raises no exceptions — returns empty list on any failure.
    """
    settings = get_settings()

    # ── Demo mode ────────────────────────────────────────────────────────────
    if settings.demo_mode:
        hid = hospital_id.upper() if hospital_id else None
        return get_demo_alerts(hid), "demo"

    # ── Live mode ─────────────────────────────────────────────────────────────
    try:
        if hospital_id:
            hospitals = [fetch_hospital_by_id(hospital_id.upper())]
            hospitals = [h for h in hospitals if h]
        else:
            hospitals = fetch_all_hospitals()

        alerts: list[dict] = []
        for hospital in hospitals:
            hid = hospital["hospital_id"]
            forecast = fetch_forecast(hid, days=7)
            alerts.extend(_alerts_from_forecast(hospital, forecast))

        return alerts, "live"

    except Exception as exc:
        logger.error("list_alerts error: %s — returning empty list", exc)
        return [], "live"


def list_alerts_for_hospital(hospital_id: str) -> tuple[list[dict], str]:
    return list_alerts(hospital_id=hospital_id)
