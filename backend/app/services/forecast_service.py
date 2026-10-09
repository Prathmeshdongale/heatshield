"""
forecast_service.py — business logic for demand forecasts.

Call chain:
  route handler
    → forecast_service.get_forecast()
        → capacity_service.get_hospital()          (for capacity_total)
        → weather_repository.fetch_weather()       (for feature inputs)
        → ml_adapter.predict()                     (per forecast day)
        → risk.calculate_risk()                    (per prediction)
        → forecast_repository.save_forecast_points()   (persist to DB)
        → forecast_repository.fetch_forecast()     (read back from DB)

DEMO MODE (DEMO_MODE=true or model not loaded):
  Returns demo data from mock_data.py. This is explicit — never a silent
  substitution when live inference was expected.

LIVE MODE (DEMO_MODE=false and model loaded):
  If the ML adapter raises ModelUnavailableError or ModelPredictionError
  the service raises ForecastUnavailableError. Routes must return 503,
  NOT substitute fabricated data.

If the hospital is not found, raises HospitalNotFoundError (404).
"""

import logging
from datetime import date, timedelta

from app.config import get_settings
from app.services.risk import calculate_risk
from app.services.capacity_service import HospitalNotFoundError
from app.repositories.hospital_repository import fetch_hospital_by_id
from app.repositories.weather_repository import fetch_weather
from app.repositories.forecast_repository import fetch_forecast, save_forecast_points
from app.integrations.ml_adapter import (
    MLFeatures,
    predict as ml_predict,
    is_model_loaded,
    get_model_version,
    ModelUnavailableError,
    ModelPredictionError,
)
from app.mock_data import HOSPITALS, get_demo_forecast

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service-level exceptions (routes map these to HTTP status codes)
# ---------------------------------------------------------------------------

# HospitalNotFoundError is imported from capacity_service (single definition)

class ForecastUnavailableError(RuntimeError):
    """
    Raised when live inference is requested but the ML model is unavailable
    or fails. Callers MUST NOT substitute fabricated data — surface 503.
    """


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_forecast(hospital_id: str, days: int) -> tuple[dict, str]:
    """
    Returns (forecast_response_dict, data_source).
    data_source: 'demo' | 'live'

    Raises:
        HospitalNotFoundError   — unknown hospital_id
        ForecastUnavailableError — live mode but model is down (→ 503)
        ValueError              — invalid days range
    """
    if not (1 <= days <= 14):
        raise ValueError(f"days must be in [1, 14], got {days}")

    settings = get_settings()
    hid = hospital_id.upper()

    # ── Demo mode ───────────────────────────────────────────────────────────
    if settings.demo_mode:
        if hid not in HOSPITALS:
            raise HospitalNotFoundError(hid)
        return get_demo_forecast(hid, days), "demo"

    # ── Live mode ────────────────────────────────────────────────────────────

    # 1. Resolve hospital (needed for capacity_total)
    hospital = fetch_hospital_by_id(hid)
    if not hospital:
        raise HospitalNotFoundError(hid)

    capacity_total = hospital.get("capacity_total")
    occupancy_pct  = hospital.get("occupancy_pct", 0.0)

    # 2. Check model is ready before doing anything expensive
    if not is_model_loaded():
        raise ForecastUnavailableError(
            "ML model is not loaded. Ensure the model artifact exists at "
            "ML_MODEL_PATH and the server has restarted after deployment."
        )

    # 3. Fetch recent weather for features (last 1 day per forecast day)
    weather_data = fetch_weather(hid, days=1)
    obs = weather_data.get("observations", [])
    latest_obs = obs[0] if obs else {}

    # 4. Run inference for each future day
    today = date.today()
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
            # Do NOT silently substitute data — propagate as service error
            logger.error("ML inference failed for %s day+%d: %s", hid, i, exc)
            raise ForecastUnavailableError(str(exc)) from exc

        risk = calculate_risk(prediction.predicted_admissions, capacity_total)

        points.append({
            "forecast_date":         str(forecast_date),
            "predicted_admissions":  round(prediction.predicted_admissions, 2),
            "confidence_lower":      round(prediction.confidence_lower, 2),
            "confidence_upper":      round(prediction.confidence_upper, 2),
            "risk_status":           risk,
        })

    model_version = get_model_version()

    # 5. Persist to DB (non-blocking failure — log and continue)
    saved = save_forecast_points(hid, points, model_version)
    if not saved:
        logger.warning("Forecast for %s was computed but could not be persisted to DB", hid)

    # 6. Return structured response
    from datetime import datetime, timezone
    return {
        "hospital_id":   hid,
        "model_version": model_version,
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "days_requested": days,
        "points":        points,
    }, "live"
