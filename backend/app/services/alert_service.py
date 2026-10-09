"""
alert_service.py — derives capacity-risk alerts from forecast data in the DB.
No demo fallback — all data comes from Supabase.

Alerts are computed on-the-fly from the forecasts table.
Any forecast point with risk_status 'red' or 'critical' generates an alert.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.repositories.forecast_repository import fetch_forecast
from app.repositories.hospital_repository import fetch_all_hospitals, fetch_hospital_by_id

logger = logging.getLogger(__name__)

_ALERT_RISK_LEVELS = {"red", "critical"}
_RISK_TO_SEVERITY  = {"red": "high", "critical": "critical"}


def _alerts_from_forecast(hospital: dict, forecast: dict) -> list[dict]:
    alerts = []
    for point in forecast.get("points", []):
        risk = point.get("risk_status", "")
        if risk not in _ALERT_RISK_LEVELS:
            continue
        alerts.append({
            "alert_id":      f"ALT-{hospital['hospital_id']}-{point['forecast_date']}",
            "hospital_id":   hospital["hospital_id"],
            "hospital_name": hospital.get("name", hospital["hospital_id"]),
            "severity":      _RISK_TO_SEVERITY[risk],
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
    Returns (alerts, 'live').
    Raises RuntimeError if DB is unreachable.
    """
    if hospital_id:
        hospitals = [fetch_hospital_by_id(hospital_id.upper())]
        hospitals = [h for h in hospitals if h]
    else:
        hospitals = fetch_all_hospitals()

    alerts: list[dict] = []
    for hospital in hospitals:
        forecast = fetch_forecast(hospital["hospital_id"], days=7)
        alerts.extend(_alerts_from_forecast(hospital, forecast))

    return alerts, "live"
