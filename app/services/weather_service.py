"""
Weather service for ThermoCare AI.

This module provides weather data fetching and processing functionality.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx
import pandas as pd
from dotenv import load_dotenv

from app.config import settings
from app.schemas.weather import WeatherData, WeatherMetrics, WeatherRequest, WeatherResponse

load_dotenv()

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching and processing weather data."""

    _instance: Optional["WeatherService"] = None

    def __new__(cls):
        """Singleton pattern for WeatherService."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize WeatherService."""
        if self._initialized:
            return
        self._initialized = True
        self.base_url = settings.weather_api_base_url
        self.api_key = settings.weather_api_key
        self.client = None

    @classmethod
    def get_instance(cls) -> "WeatherService":
        """Get the singleton instance of WeatherService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def fetch_weather_data(self, request: WeatherRequest) -> WeatherResponse:
        """
        Fetch weather data for a location and date range.

        Args:
            request: WeatherRequest with location, date range, and options

        Returns:
            WeatherResponse with weather data list
        """
        logger.info(f"Fetching weather data for {request.location} from {request.start_date} to {request.end_date}")

        if not self.base_url:
            raise ValueError("Weather API base URL not configured")

        # In production, this would call the actual weather API
        # For now, return a placeholder response
        weather_data = [
            WeatherData(
                location=request.location,
                timestamp=request.start_date,
                metrics=WeatherMetrics(
                    temperature=25.0,
                    humidity=60.0,
                    wind_speed=10.0,
                    wind_direction=180,
                    pressure=1013.0,
                    precipitation=0.0,
                    uv_index=5.0,
                ),
                source="placeholder",
                quality_score=1.0,
            )
        ]

        return WeatherResponse(
            location=request.location,
            data=weather_data,
            metadata={"total_records": len(weather_data), "source": "placeholder"},
        )

    async def fetch_historical_weather(
        self,
        location: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """
        Fetch historical weather data as a DataFrame.

        Args:
            location: Location identifier
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            DataFrame with historical weather data
        """
        logger.info(f"Fetching historical weather for {location}")

        # Placeholder implementation
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        data = {
            "timestamp": dates,
            "temperature": [20 + i * 0.1 for i in range(len(dates))],
            "humidity": [60] * len(dates),
            "wind_speed": [10] * len(dates),
        }
        return pd.DataFrame(data)

    async def get_weather_alerts(self, location: str) -> list[dict]:
        """
        Get weather alerts for a location.

        Args:
            location: Location identifier

        Returns:
            List of weather alert dictionaries
        """
        logger.info(f"Checking weather alerts for {location}")
        return []

    def parse_weather_condition(self, condition_code: int) -> str:
        """
        Parse weather condition code to human-readable string.

        Args:
            condition_code: Weather condition code

        Returns:
            Human-readable weather condition
        """
        conditions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with heavy hail",
        }
        return conditions.get(condition_code, "Unknown")
