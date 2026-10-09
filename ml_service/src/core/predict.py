"""
predict.py — Generate predictions (single, batch, with confidence intervals).
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Predictor:
    """Generate predictions using a trained scikit-learn model."""

    def __init__(self, model: Optional[object] = None):
        self.model = model

    def set_model(self, model: object) -> None:
        self.model = model
        logger.info("Model set for prediction")

    # ── Point predictions ─────────────────────────────────────────────────────

    def predict_single(self, features: np.ndarray) -> float:
        if self.model is None:
            raise ValueError("No model set for prediction")
        return max(0.0, float(self.model.predict(features.reshape(1, -1))[0]))

    def predict_batch(self, features: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ValueError("No model set for prediction")
        return np.maximum(0, self.model.predict(features))

    # ── Confidence intervals ─────────────────────────────────────────────────

    def predict_with_confidence(
        self,
        features: np.ndarray,
        confidence_level: float = 0.95,
    ) -> Dict[str, np.ndarray]:
        predictions = self.predict_batch(features)
        margin = predictions * 0.1          # ±10% placeholder
        return {
            "predictions": predictions,
            "lower":       np.maximum(0, predictions - margin),
            "upper":       predictions + margin,
        }

    # ── Series forecast ───────────────────────────────────────────────────────

    def generate_forecast_series(
        self,
        features_df: pd.DataFrame,
        timestamp_column: str = "timestamp",
    ) -> pd.DataFrame:
        features = features_df.drop(columns=[timestamp_column]).values
        predictions = self.predict_batch(features)
        result = features_df[[timestamp_column]].copy()
        result["predicted_demand"]   = predictions
        result["confidence_lower"]   = np.maximum(0, predictions * 0.9)
        result["confidence_upper"]   = predictions * 1.1
        return result

    # ── Error metrics ─────────────────────────────────────────────────────────

    def calculate_prediction_error(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, float]:
        abs_err = np.abs(y_true - y_pred)
        sq_err  = (y_true - y_pred) ** 2
        return {
            "mae":       float(np.mean(abs_err)),
            "rmse":      float(np.sqrt(np.mean(sq_err))),
            "mape":      float(np.mean(abs_err / np.maximum(y_true, 1e-6))),
            "max_error": float(np.max(abs_err)),
        }
