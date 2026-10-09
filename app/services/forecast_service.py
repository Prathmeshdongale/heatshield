"""
Forecast service for ThermoCare AI.

This module provides healthcare demand forecasting functionality.
"""

import logging
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
from joblib import load

from app.config import settings
from app.ml.model_registry import ModelRegistry
from app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastBatchResponse

logger = logging.getLogger(__name__)


class ForecastService:
    """Service for generating healthcare demand forecasts."""

    _instance: Optional["ForecastService"] = None

    def __new__(cls):
        """Singleton pattern for ForecastService."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize ForecastService."""
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls) -> "ForecastService":
        """Get the singleton instance of ForecastService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_forecast(
        self,
        request: ForecastRequest,
        model_registry: ModelRegistry,
    ) -> ForecastResponse:
        """
        Generate healthcare demand forecast.

        Args:
            request: ForecastRequest with location and weather parameters
            model_registry: ModelRegistry with loaded model

        Returns:
            ForecastResponse with prediction and confidence intervals
        """
        self.logger.info(f"Generating forecast for {request.location} on {request.date}")

        # Get model
        model = model_registry.get_model()
        if model is None:
            raise ValueError("No model loaded")

        # Create feature vector
        features = self._create_features(request)

        # Make prediction
        prediction = model.predict(features.reshape(1, -1))[0]

        # Get confidence intervals
        confidence_interval = self._calculate_confidence_interval(model_registry, prediction)

        # Determine risk level
        risk_level = self._determine_risk_level(prediction)

        return ForecastResponse(
            date=request.date,
            location=request.location,
            predicted_demand=prediction,
            confidence_lower=confidence_interval[0],
            confidence_upper=confidence_interval[1],
            risk_level=risk_level,
            generated_at=pd.Timestamp.now(),
            model_version=model_registry.get_model_version(),
        )

    async def generate_batch_forecast(
        self,
        requests: list[ForecastRequest],
        model_registry: ModelRegistry,
    ) -> ForecastBatchResponse:
        """
        Generate multiple forecasts.

        Args:
            requests: List of ForecastRequest objects
            model_registry: ModelRegistry with loaded model

        Returns:
            ForecastBatchResponse with all forecasts
        """
        self.logger.info(f"Generating batch forecast for {len(requests)} requests")

        forecasts = []
        for request in requests:
            try:
                forecast = await self.generate_forecast(request, model_registry)
                forecasts.append(forecast)
            except Exception as e:
                self.logger.error(f"Failed to generate forecast for {request.location}: {e}")
                continue

        return ForecastBatchResponse(
            forecasts=forecasts,
            total_count=len(requests),
            success_count=len(forecasts),
            failed_count=len(requests) - len(forecasts),
        )

    def _create_features(self, request: ForecastRequest) -> np.ndarray:
        """
        Create feature vector from request.

        Args:
            request: ForecastRequest

        Returns:
            NumPy array of features
        """
        # Basic features from request
        features = np.array([
            request.temperature,
            request.humidity,
            # Add more features as needed
        ])
        return features

    def _calculate_confidence_interval(
        self,
        model_registry: ModelRegistry,
        prediction: float,
    ) -> tuple[float, float]:
        """
        Calculate confidence interval for prediction.

        Args:
            model_registry: ModelRegistry with model statistics
            prediction: Point prediction

        Returns:
            Tuple of (lower, upper) confidence bounds
        """
        # Placeholder: use fixed confidence interval
        margin = prediction * 0.1  # 10% margin
        return (max(0, prediction - margin), prediction + margin)

    def _determine_risk_level(self, demand: float) -> str:
        """
        Determine risk level based on demand prediction.

        Args:
            demand: Predicted demand

        Returns:
            Risk level string: low, medium, high, or critical
        """
        # Placeholder: use demand thresholds
        if demand < 100:
            return "low"
        elif demand < 500:
            return "medium"
        elif demand < 1000:
            return "high"
        else:
            return "critical"
