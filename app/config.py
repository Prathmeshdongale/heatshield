"""
Configuration management for ThermoCare AI.

This module loads environment variables and provides configuration
classes for the application using Pydantic settings.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Environment
    app_env: str = Field(default="development", description="Application environment (development/production)")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

    # Model Configuration
    model_dir: str = Field(default="data/models", description="Model storage directory")
    data_dir: str = Field(default="data", description="Data directory root")
    reports_dir: str = Field(default="data/reports", description="Reports directory")

    # Default Location (London, England)
    default_latitude: float = Field(default=51.5074, description="Default latitude for London, England")
    default_longitude: float = Field(default=-0.1278, description="Default longitude for London, England")
    default_timezone: str = Field(default="Europe/London", description="Default timezone")

    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="List of allowed origins for CORS"
    )

    # Weather Provider Configuration
    weather_provider: str = Field(default="met_office", description="Weather provider (met_office, openweathermap, visualcrossing)")
    forecast_horizon_days: int = Field(default=7, description="Number of days for weather forecast", ge=1, le=14)

    # Feature Engineering Configuration
    target_column: str = Field(default="ed_visits_heat", description="Target column name for heat-related ED visits")
    date_column: str = Field(default="date", description="Date column name")
    lag_days: List[int] = Field(default=[1, 2, 3, 7], description="Lag days for time-series features")
    rolling_windows: List[int] = Field(default=[3, 7, 14], description="Rolling window sizes")
    
    # Temperature features
    temperature_column: str = Field(default="temp_mean", description="Mean temperature column")
    temp_max_column: str = Field(default="temp_max", description="Max temperature column")
    temp_min_column: str = Field(default="temp_min", description="Min temperature column")
    
    # Heatwave thresholds
    heatwave_temp_threshold: float = Field(default=28.0, description="Temperature threshold for heatwave (°C)")
    heatwave_duration_days: int = Field(default=3, description="Minimum days for heatwave")
    
    # Weather features
    humidity_column: str = Field(default="humidity", description="Humidity column")
    precipitation_column: str = Field(default="precipitation", description="Precipitation column")
    wind_speed_column: str = Field(default="wind_speed", description="Wind speed column")
    
    # Missing data strategy
    missing_weather_strategy: str = Field(default="mean", description="Strategy for missing weather data (mean, forward_fill, backward_fill)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level (DEBUG/INFO/WARNING/ERROR)")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @property
    def base_dir(self) -> Path:
        """Get the base project directory."""
        return Path(__file__).parent.parent

    @property
    def model_path(self) -> Path:
        """Get the absolute path to model directory."""
        return self.base_dir / self.model_dir

    @property
    def data_path(self) -> Path:
        """Get the absolute path to data directory."""
        return self.base_dir / self.data_dir

    @property
    def reports_path(self) -> Path:
        """Get the absolute path to reports directory."""
        return self.base_dir / self.reports_dir

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env.lower() == "development"


# Global settings instance
settings = Settings()
