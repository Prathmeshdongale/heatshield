"""
forecast_service.py — Demand forecasts using the trained HeatShield model.

When model is loaded: runs live GradientBoosting inference → persists to DB.
When model is absent: serves pre-seeded DB rows (no 503).
"""

import logging
from datetime import date, datetime, timedelta, timezone

from app.services.risk import calculate_risk
from app.services.capacity_service import HospitalNotFoundError
from app.repositories.hospital_repository import fetch_hospital_by_id
from app.repositories.weather_repository import fetch_weather
from app.repositories.forecast_repository import fetch_forecast, save_forecast_points
from app.integrations.ml_adapter import (
    MLFeatures,
    MLPrediction,
    predict as ml_predict,
    is_model_loaded,
    get_model_version,
    ModelUnavailableError,
    ModelPredictionError,
)
from app.integrations.supabase_client import is_db_available

logger = logging.getLogger(__name__)


class ForecastUnavailableError(RuntimeError):
    """Model loaded but inference failed — surface as 503."""


def get_forecast(hospital_id: str, days: int) -> tuple[dict, str]:
    """
    Returns (forecast_dict, 'live').

    Raises:
        HospitalNotFoundError    — unknown hospital
        ForecastUnavailableError — model loaded but inference failed
        ValueError               — days out of [1,14]
        RuntimeError             — DB unreachable
    """
    if not (1 <= days <= 14):
        raise ValueError(f"days must be in [1,14], got {days}")

    hid = hospital_id.upper()

    # Resolve hospital
    hospital = fetch_hospital_by_id(hid)
    if not hospital:
        raise HospitalNotFoundError(hid)

    # No model → serve stored DB rows
    if not is_model_loaded():
        logger.info("ML model not loaded for %s — serving stored DB forecasts", hid)
        stored = fetch_forecast(hid, days)
        source = "live" if is_db_available() else "demo"
        return stored, source

    # ── Live inference ────────────────────────────────────────────────────────
    capacity_total  = hospital.get("capacity_total", 500)
    bed_occ         = hospital.get("occupancy_pct", 80.0)

    # Fetch latest weather observation for feature values
    weather_data = fetch_weather(hid, days=1)
    obs = weather_data.get("observations", [])
    w = obs[0] if obs else {}

    today = date.today()
    points: list[dict] = []

    for i in range(1, days + 1):
        fdate = today + timedelta(days=i)
        season_map = {12:0,1:0,2:0, 3:1,4:1,5:1, 6:2,7:2,8:2, 9:3,10:3,11:3}

        features = MLFeatures(
            tmax_c               = float(w.get("temperature_max_c", 20.0)),
            tmin_c               = float(w.get("temperature_min_c", 12.0)),
            humidity_pct         = float(w.get("humidity_pct", 65.0)),
            heat_index_c         = float(w.get("heat_index_c", 20.0)),
            uv_index             = float(w.get("uv_index", 2.0)),
            pm25_ugm3            = float(w.get("pm25_ugm3", 10.0)),
            ozone_ugm3           = float(w.get("ozone_ugm3", 40.0)),
            warm_night_flag      = float(w.get("warm_night_flag", 0)),
            consecutive_hot_days = float(w.get("consecutive_hot_days", 0)),
            heatwave_flag        = float(w.get("heatwave_flag", 0)),
            day_of_week          = fdate.weekday(),
            is_bank_holiday      = 0,
            general_acute_beds   = int(capacity_total),
            icu_beds             = int(hospital.get("icu_beds", 20)),
            ambulances_available = int(hospital.get("ambulances_available", 15)),
            baseline_staff_per_shift = int(hospital.get("baseline_staff_per_shift", 300)),
            bed_occupancy_pct    = float(bed_occ),
            pct_pop_over_65      = float(hospital.get("pct_pop_over_65", 18.0)),
            pct_pop_under_5      = float(hospital.get("pct_pop_under_5", 5.0)),
            imd_deprivation_decile = int(hospital.get("imd_deprivation_decile", 5)),
            green_space_pct      = float(hospital.get("green_space_pct", 25.0)),
            ac_cooled_wards_pct  = float(hospital.get("ac_cooled_wards_pct", 40.0)),
            heat_health_alert_enc = 1 if float(w.get("heat_index_c", 0)) > 35 else 0,
            month                = fdate.month,
            is_weekend           = int(fdate.weekday() >= 5),
            season               = season_map.get(fdate.month, 2),
            # Use current occupancy as proxy for lag values
            ae_lag_1             = float(bed_occ * capacity_total / 100 * 0.3),
            ae_lag_3             = float(bed_occ * capacity_total / 100 * 0.3),
            ae_lag_7             = float(bed_occ * capacity_total / 100 * 0.3),
            ae_roll_3            = float(bed_occ * capacity_total / 100 * 0.3),
            ae_roll_7            = float(bed_occ * capacity_total / 100 * 0.3),
        )

        try:
            pred = ml_predict(features)
        except (ModelUnavailableError, ModelPredictionError) as exc:
            logger.error("ML inference failed for %s day+%d: %s", hid, i, exc)
            raise ForecastUnavailableError(str(exc)) from exc

        risk = calculate_risk(pred.predicted_admissions, capacity_total)
        points.append({
            "forecast_date":        str(fdate),
            "predicted_admissions": pred.predicted_admissions,
            "confidence_lower":     pred.confidence_lower,
            "confidence_upper":     pred.confidence_upper,
            "risk_status":          risk,
        })

    model_version = get_model_version()
    save_forecast_points(hid, points, model_version)

    return {
        "hospital_id":    hid,
        "model_version":  model_version,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "days_requested": days,
        "points":         points,
    }, "live"
