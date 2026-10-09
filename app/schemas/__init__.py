"""
Pydantic schemas for ThermoCare AI.

This package contains data validation models for API requests and responses.
"""

from app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastBatchRequest, ForecastBatchResponse
from app.schemas.hospital import HospitalMetrics, HospitalData, HospitalDemandProjection, ResourceRecommendation
from app.schemas.weather import WeatherData, WeatherMetrics, WeatherRequest, WeatherResponse, WeatherAlert, WeatherStation

__all__ = [
    "ForecastRequest",
    "ForecastResponse",
    "ForecastBatchRequest",
    "ForecastBatchResponse",
    "HospitalMetrics",
    "HospitalData",
    "HospitalDemandProjection",
    "ResourceRecommendation",
    "WeatherData",
    "WeatherMetrics",
    "WeatherRequest",
    "WeatherResponse",
    "WeatherAlert",
    "WeatherStation",
]
