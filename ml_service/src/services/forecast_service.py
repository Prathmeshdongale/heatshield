"""
forecast_service.py — Generate demand forecasts using the trained model.
"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.core.model_registry import ModelRegistry
from src.schemas.forecast import ForecastRequest, ForecastResponse, ForecastBatchResponse

logger = logging.getLogger(__name__)


class ForecastService:
    """Singleton service for demand forecasting."""

    _instance: Optional["ForecastService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "ForecastService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_forecast(
        self,
        request: ForecastRequest,
        model_registry: ModelRegistry,
    ) -> ForecastResponse:
        model = model_registry.get_model()
        if model is None:
            raise ValueError("No model loaded")

        features = np.array([
            request.temperature,
            request.humidity,
        ])
        prediction = max(0.0, float(model.predict(features.reshape(1, -1))[0]))
        margin = prediction * 0.15

        return ForecastResponse(
            date=request.date,
            location=request.location,
            predicted_demand=round(prediction, 2),
            confidence_lower=round(max(0, prediction - margin), 2),
            confidence_upper=round(prediction + margin, 2),
            risk_level=self._risk(prediction),
            generated_at=datetime.utcnow(),
            model_version=model_registry.get_model_version() or "v1.0.0",
        )

    async def generate_batch_forecast(
        self,
        requests: list[ForecastRequest],
        model_registry: ModelRegistry,
    ) -> ForecastBatchResponse:
        forecasts, failed = [], 0
        for req in requests:
            try:
                forecasts.append(await self.generate_forecast(req, model_registry))
            except Exception as exc:
                logger.error("Forecast failed for %s: %s", req.location, exc)
                failed += 1
        return ForecastBatchResponse(
            forecasts=forecasts,
            total_count=len(requests),
            success_count=len(forecasts),
            failed_count=failed,
        )

    @staticmethod
    def _risk(demand: float) -> str:
        if demand < 80:   return "low"
        if demand < 120:  return "medium"
        if demand < 200:  return "high"
        return "critical"
