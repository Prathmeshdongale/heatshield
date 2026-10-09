"""
Prediction module for ThermoCare AI.

This module provides functionality for generating predictions using trained models.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Predictor:
    """Class for generating predictions using ML models."""

    def __init__(self, model: Optional[object] = None):
        """
        Initialize Predictor.

        Args:
            model: Trained ML model (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.model = model

    def set_model(self, model: object) -> None:
        """
        Set the prediction model.

        Args:
            model: Trained ML model
        """
        self.model = model
        self.logger.info("Model set for prediction")

    def predict_single(
        self,
        features: np.ndarray,
    ) -> float:
        """
        Generate prediction for a single sample.

        Args:
            features: Feature vector

        Returns:
            Predicted value
        """
        if self.model is None:
            raise ValueError("No model set for prediction")

        prediction = self.model.predict(features.reshape(1, -1))[0]
        return max(0, prediction)  # Ensure non-negative

    def predict_batch(
        self,
        features: np.ndarray,
    ) -> np.ndarray:
        """
        Generate predictions for multiple samples.

        Args:
            features: Features matrix (n_samples, n_features)

        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("No model set for prediction")

        predictions = self.model.predict(features)
        return np.maximum(0, predictions)  # Ensure non-negative

    def predict_with_confidence(
        self,
        features: np.ndarray,
        confidence_level: float = 0.95,
    ) -> dict[str, np.ndarray]:
        """
        Generate predictions with confidence intervals.

        Args:
            features: Features matrix
            confidence_level: Confidence level (0-1)

        Returns:
            Dictionary with predictions and confidence intervals
        """
        predictions = self.predict_batch(features)

        # Placeholder: calculate simple confidence intervals
        # In production, use proper uncertainty estimation
        margin = predictions * 0.1  # 10% margin
        lower = np.maximum(0, predictions - margin)
        upper = predictions + margin

        return {
            "predictions": predictions,
            "lower": lower,
            "upper": upper,
        }

    def generate_forecast_series(
        self,
        features_df: pd.DataFrame,
        timestamp_column: str = "timestamp",
    ) -> pd.DataFrame:
        """
        Generate forecast series from DataFrame.

        Args:
            features_df: DataFrame with features and timestamps
            timestamp_column: Name of timestamp column

        Returns:
            DataFrame with predictions and timestamps
        """
        features = features_df.drop(columns=[timestamp_column]).values
        predictions = self.predict_batch(features)

        result = features_df[[timestamp_column]].copy()
        result["predicted_demand"] = predictions
        result["confidence_lower"] = np.maximum(0, predictions * 0.9)
        result["confidence_upper"] = predictions * 1.1

        return result

    def calculate_prediction_error(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> dict[str, float]:
        """
        Calculate prediction errors.

        Args:
            y_true: True values
            y_pred: Predicted values

        Returns:
            Dictionary of error metrics
        """
        absolute_errors = np.abs(y_true - y_pred)
        squared_errors = (y_true - y_pred) ** 2

        return {
            "mae": float(np.mean(absolute_errors)),
            "rmse": float(np.sqrt(np.mean(squared_errors))),
            "mape": float(np.mean(absolute_errors / np.maximum(y_true, 1e-6))),
            "max_error": float(np.max(absolute_errors)),
        }
