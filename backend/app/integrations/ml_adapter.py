"""
ml_adapter.py — Backend interface to the trained HeatShield ML model.

Trained on datasets/nhs_heat_hospital_demand_synthetic.csv
Algorithm: GradientBoostingRegressor, 31 features, target: ae_attendances.
Feature order MUST match train_model.py exactly.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# Absolute path derived from this file's location — works regardless of cwd
_DEFAULT_ARTIFACT = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "model.joblib"

# ── Feature contract ──────────────────────────────────────────────────────────

FEATURE_ORDER = [
    "tmax_c", "tmin_c", "humidity_pct", "heat_index_c",
    "uv_index", "pm25_ugm3", "ozone_ugm3",
    "warm_night_flag", "consecutive_hot_days", "heatwave_flag",
    "day_of_week", "is_bank_holiday",
    "general_acute_beds", "icu_beds", "ambulances_available",
    "baseline_staff_per_shift", "bed_occupancy_pct",
    "pct_pop_over_65", "pct_pop_under_5", "imd_deprivation_decile",
    "green_space_pct", "ac_cooled_wards_pct",
    "heat_health_alert_enc", "month", "is_weekend", "season",
    "ae_lag_1", "ae_lag_3", "ae_lag_7",
    "ae_roll_3", "ae_roll_7",
]


@dataclass
class MLFeatures:
    """31 input features in exact training order. Defaults are sensible for missing data."""
    tmax_c:                   float = 20.0
    tmin_c:                   float = 12.0
    humidity_pct:              float = 65.0
    heat_index_c:              float = 20.0
    uv_index:                  float = 2.0
    pm25_ugm3:                 float = 10.0
    ozone_ugm3:                float = 40.0
    warm_night_flag:           float = 0.0
    consecutive_hot_days:      float = 0.0
    heatwave_flag:             float = 0.0
    day_of_week:               int   = 0
    is_bank_holiday:           int   = 0
    general_acute_beds:        int   = 500
    icu_beds:                  int   = 20
    ambulances_available:      int   = 15
    baseline_staff_per_shift:  int   = 300
    bed_occupancy_pct:         float = 80.0
    pct_pop_over_65:           float = 18.0
    pct_pop_under_5:           float = 5.0
    imd_deprivation_decile:    int   = 5
    green_space_pct:           float = 25.0
    ac_cooled_wards_pct:       float = 40.0
    heat_health_alert_enc:     int   = 0
    month:                     int   = 7
    is_weekend:                int   = 0
    season:                    int   = 2
    ae_lag_1:                  float = 100.0
    ae_lag_3:                  float = 100.0
    ae_lag_7:                  float = 100.0
    ae_roll_3:                 float = 100.0
    ae_roll_7:                 float = 100.0

    def to_list(self) -> list:
        return [getattr(self, f) for f in FEATURE_ORDER]


@dataclass
class MLPrediction:
    predicted_admissions: float
    confidence_lower:     float
    confidence_upper:     float


# ── Exceptions ────────────────────────────────────────────────────────────────

class ModelUnavailableError(RuntimeError):
    """Model not loaded — caller should not fabricate data."""

class ModelPredictionError(RuntimeError):
    """Model raised during inference."""


# ── Module-level state ────────────────────────────────────────────────────────

_model         = None
_model_version: str = "unknown"


def _resolve_artifact_path() -> str:
    """
    Return the absolute path to the model artifact.
    Tries (in order):
      1. settings.ml_model_path_abs  (from .env)
      2. _DEFAULT_ARTIFACT           (relative to this file — always works)
    """
    try:
        settings = get_settings()
        candidate = Path(settings.ml_model_path_abs)
        if candidate.exists():
            return str(candidate)
    except Exception:
        pass

    return str(_DEFAULT_ARTIFACT)


def load_model() -> None:
    """
    Load the joblib model at startup. Non-fatal if the file is missing.
    Uses file-relative path as the primary strategy so it works even when
    uvicorn's --reload mode changes the working directory.
    """
    global _model, _model_version

    path = _resolve_artifact_path()

    if not os.path.exists(path):
        logger.warning(
            "ML model not found at '%s' — backend will serve DB forecasts.", path
        )
        return

    try:
        import joblib
        loaded = joblib.load(path)
        _model = loaded
        _model_version = getattr(loaded, "version", "v1.0.0")
        logger.info("✓ ML model loaded: %s  version=%s", path, _model_version)
    except Exception as exc:
        logger.error("Failed to load ML model from '%s': %s", path, exc)


def is_model_loaded() -> bool:
    return _model is not None


def get_model_version() -> str:
    return _model_version


def predict(features: MLFeatures) -> MLPrediction:
    """
    Run inference for one sample.
    Raises ModelUnavailableError if model not loaded.
    Raises ModelPredictionError on inference failure.
    """
    if _model is None:
        raise ModelUnavailableError("ML model is not loaded.")

    try:
        import pandas as pd
        # Use DataFrame with named columns to match training — silences sklearn warning
        row_df = pd.DataFrame([features.to_list()], columns=FEATURE_ORDER)
        raw = _model.predict(row_df)
        pred = max(float(raw[0]), 0.0)
        return MLPrediction(
            predicted_admissions=round(pred, 2),
            confidence_lower=round(pred * 0.85, 2),
            confidence_upper=round(pred * 1.15, 2),
        )
    except ModelUnavailableError:
        raise
    except Exception as exc:
        raise ModelPredictionError(f"Inference error: {exc}") from exc


def reset_model() -> None:
    """Reset state — used in tests only."""
    global _model, _model_version
    _model = None
    _model_version = "unknown"
