"""
forecast_service.py — demand forecasts from the real database.
No demo fallback — all data comes from Supabase (seeded or ML-generated).

When the ML model is not loaded, the service returns pre-seeded forecast rows
from the DB. When the model IS loaded, it runs inference and persists the result.
If inference fails, raises ForecastUnavailableError (→ 503).
"""

import logging
from datetime import date, timedelta

from app.services.risk import calculate_risk
from app.services.capacity_service import HospitalNotFoundError
from app.repositories.hospital_repository import fetch_hospital_by_id
from app.repositories.weather_repository import fetch_weather
from app.repositories.forecast_repository import fetch_forecast, save_forecast_points
from app.integrations.supabase_client import is_db_available
from app.integrations.ml_adapter import (
    MLFeatures,
    predict as ml_predict,
    is_model_loaded,
    get_model_version,
    ModelUnavailableError,
    ModelPredictionError,
)

logger = logging.getLogger(__name__)


class ForecastUnavailableError(RuntimeError):
    """ML inference was attempted but failed. Surface as 503."""


def get_forecast(hospital_id: str, days: int) -> tuple[dict, str]:
    """
    Returns (forecast_dict, 'live').

    If the ML model is not loaded, returns stored forecast rows from the DB.
    If the model IS loaded, runs inference, persists, and returns fresh rows.

    Raises:
        HospitalNotFoundError   — hospital not in DB
        ForecastUnavailableError — model loaded but inference failed
        ValueError              — days out of range
        RuntimeError            — DB unreachable
    """
    if not (1 <= days <= 14):
        raise ValueError(f"days must be in [1, 14], got {days}")

    hid = hospital_id.upper()

    # 1. Resolve hospital
    hospital = fetch_hospital_by_id(hid)
    if not hospital:
        raise HospitalNotFoundError(hid)

    # 2. No ML model → serve stored DB rows (seeded demo data counts as "live")
    if not is_model_loaded():
        logger.info("ML model not loaded for %s — serving stored DB forecasts", hid)
        stored = fetch_forecast(hid, days)
        db_live = is_db_available()
        return stored, "live" if db_live else "demo"

    # 3. ML model available — run inference
    capacity_total = hospital.get("capacity_total")
    occupancy_pct  = hospital.get("occupancy_pct", 0.0)

    weather_data = fetch_weather(hid, days=1)
    obs = weather_data.get("observations", [])
    latest_obs = obs[0] if obs else {}

    today  = date.today()
    points: list[dict] = []

    for i in range(1, days + 1):
        forecast_date = today + timedelta(days=i)
        features = MLFeatures(
            temperature_max_c = float(latest_obs.get("temperature_max_c", 25.0)),
            temperature_min_c = float(latest_obs.get("temperature_min_c", 15.0)),
            humidity_pct      = float(latest_obs.get("humidity_pct", 60.0)),
            heat_index_c      = float(latest_obs.get("heat_index_c", 27.0)),
            occupancy_pct     = float(occupancy_pct),
            capacity_total    = int(capacity_total) if capacity_total else 0,
            day_of_week       = forecast_date.weekday(),
            month             = forecast_date.month,
        )
        try:
            prediction = ml_predict(features)
        except (ModelUnavailableError, ModelPredictionError) as exc:
            logger.error("ML inference failed for %s day+%d: %s", hid, i, exc)
            raise ForecastUnavailableError(str(exc)) from exc

        risk = calculate_risk(prediction.predicted_admissions, capacity_total)
        points.append({
            "forecast_date":        str(forecast_date),
            "predicted_admissions": round(prediction.predicted_admissions, 2),
            "confidence_lower":     round(prediction.confidence_lower, 2),
            "confidence_upper":     round(prediction.confidence_upper, 2),
            "risk_status":          risk,
        })

    model_version = get_model_version()
    save_forecast_points(hid, points, model_version)

    from datetime import datetime, timezone
    return {
        "hospital_id":    hid,
        "model_version":  model_version,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "days_requested": days,
        "points":         points,
    }, "live"
