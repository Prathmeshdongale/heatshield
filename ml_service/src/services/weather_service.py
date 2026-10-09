"""weather_service.py — Weather data fetching and processing."""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from src.schemas.weather import WeatherData, WeatherMetrics, WeatherRequest, WeatherResponse

logger = logging.getLogger(__name__)


class WeatherService:
    _instance: Optional["WeatherService"] = None

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
    def get_instance(cls) -> "WeatherService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def fetch_weather_data(self, request: WeatherRequest) -> WeatherResponse:
        """Fetch weather data (stub — connects to real API in production)."""
        logger.info("Fetching weather for %s", request.location)
        weather_data = [
            WeatherData(
                location=request.location,
                timestamp=request.start_date,
                metrics=WeatherMetrics(
                    temperature=20.0, humidity=65.0, wind_speed=10.0,
                    wind_direction=180, pressure=1013.0, precipitation=0.0, uv_index=3.0,
                ),
                source="placeholder",
                quality_score=1.0,
            )
        ]
        return WeatherResponse(
            location=request.location,
            data=weather_data,
            metadata={"total_records": len(weather_data)},
        )

    async def fetch_historical_weather(
        self, location: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        return pd.DataFrame({
            "timestamp":   dates,
            "temperature": [20 + i * 0.1 for i in range(len(dates))],
            "humidity":    [65] * len(dates),
            "wind_speed":  [10] * len(dates),
        })
