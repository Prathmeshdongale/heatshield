"""
ml_adapter.py — interface between the backend and the ML model artifact.

CONTRACT WITH MEMBER 2 (ML team)
─────────────────────────────────
Input feature dict (keys and order must be stable — change requires
coordination with Member 2 before any field is added/removed/renamed):

    {
        "temperature_max_c":   float,   # daily max air temperature
        "temperature_min_c":   float,   # daily min air temperature
        "humidity_pct":        float,   # relative humidity 0–100
        "heat_index_c":        float,   # apparent temperature
        "occupancy_pct":       float,   # current bed occupancy 0–100
        "capacity_total":      int,     # total beds
        "day_of_week":         int,     # 0=Monday … 6=Sunday
        "month":               int,     # 1–12
    }

Output dict (returned by predict()):

    {
        "predicted_admissions": float,   # point estimate ≥ 0
        "confidence_lower":     float,   # lower bound of 90 % CI
        "confidence_upper":     float,   # upper bound of 90 % CI
    }

Model artifact:  joblib-serialised sklearn Pipeline or compatible object
                 located at the path in settings.ml_model_path.

FAILURE MODES
─────────────
- Model file missing at startup      → logged warning; model stays None
- predict() called with model=None   → raises ModelUnavailableError
- predict() raises any other error   → propagates as ModelPredictionError
  Callers MUST NOT silently substitute fabricated values on these errors.
"""

import os
import logging
from dataclasses import dataclass
from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Typed input / output so callers get IDE help and the contract is explicit
# ---------------------------------------------------------------------------

@dataclass
class MLFeatures:
    temperature_max_c:  float
    temperature_min_c:  float
    humidity_pct:       float
    heat_index_c:       float
    occupancy_pct:      float
    capacity_total:     int
    day_of_week:        int   # 0=Monday … 6=Sunday
    month:              int   # 1–12

    def to_list(self) -> list:
        """Return features in the exact order the model was trained on."""
        return [
            self.temperature_max_c,
            self.temperature_min_c,
            self.humidity_pct,
            self.heat_index_c,
            self.occupancy_pct,
            self.capacity_total,
            self.day_of_week,
            self.month,
        ]


@dataclass
class MLPrediction:
    predicted_admissions: float
    confidence_lower:     float
    confidence_upper:     float


# ---------------------------------------------------------------------------
# Custom exceptions — callers check for these, not generic Exception
# ---------------------------------------------------------------------------

class ModelUnavailableError(RuntimeError):
    """Raised when predict() is called but no model is loaded."""


class ModelPredictionError(RuntimeError):
    """Raised when the model raises an unexpected error during inference."""


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_model = None
_model_version: str = "unknown"


def load_model() -> None:
    """
    Load the joblib model from disk (called once at startup via lifespan).
    Logs a warning if the artifact is absent — does NOT raise.
    """
    global _model, _model_version
    settings = get_settings()
    path = settings.ml_model_path

    if not os.path.exists(path):
        logger.warning(
            "ML model artifact not found at '%s'. "
            "Live inference is unavailable — demo mode will be used.",
            path,
        )
        return

    try:
        import joblib
        loaded = joblib.load(path)
        _model = loaded
        # Convention with Member 2: artifact exposes a .version attribute;
        # fall back gracefully if it does not.
        _model_version = getattr(loaded, "version", "loaded")
        logger.info("ML model loaded from '%s' (version=%s)", path, _model_version)
    except Exception as exc:
        logger.error("Failed to load ML model from '%s': %s", path, exc)


def is_model_loaded() -> bool:
    return _model is not None


def get_model_version() -> str:
    return _model_version


def predict(features: MLFeatures) -> MLPrediction:
    """
    Run inference for a single day's features.

    Raises:
        ModelUnavailableError  — model not loaded (missing artifact / startup failure)
        ModelPredictionError   — model raised an error during inference
    """
    if _model is None:
        raise ModelUnavailableError(
            "ML model is not loaded. Check ML_MODEL_PATH and restart the server."
        )

    try:
        raw = _model.predict([features.to_list()])

        # Member 2 convention: model returns a 2-D array where each row is
        # [predicted_admissions, confidence_lower, confidence_upper].
        # If the model returns a 1-D array it is treated as the point estimate
        # with ±15 % symmetric bounds (temporary until CI columns are added).
        row = raw[0]
        if hasattr(row, "__len__") and len(row) >= 3:
            pred   = float(row[0])
            lower  = float(row[1])
            upper  = float(row[2])
        else:
            pred  = float(row)
            lower = round(pred * 0.85, 2)
            upper = round(pred * 1.15, 2)

        return MLPrediction(
            predicted_admissions=max(pred, 0.0),
            confidence_lower=max(lower, 0.0),
            confidence_upper=max(upper, 0.0),
        )

    except ModelUnavailableError:
        raise
    except Exception as exc:
        raise ModelPredictionError(
            f"Model raised an error during inference: {exc}"
        ) from exc


def reset_model() -> None:
    """Reset model state — used in tests only."""
    global _model, _model_version
    _model = None
    _model_version = "unknown"
