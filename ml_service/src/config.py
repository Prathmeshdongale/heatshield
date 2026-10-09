"""
config.py — ML Service settings loaded from environment variables.
All modules import `settings` from here.
"""
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    app_env: str = Field(default="development")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8001)

    # Directories (relative to project root)
    model_dir: str = Field(default="data/models")
    data_dir: str = Field(default="data")
    reports_dir: str = Field(default="data/reports")

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # Feature engineering
    target_column: str = Field(default="ae_attendances")   # matches NHS dataset
    date_column: str = Field(default="date")
    lag_days: List[int] = Field(default=[1, 2, 3, 7])
    rolling_windows: List[int] = Field(default=[3, 7, 14])

    # Temperature / weather columns
    temperature_column: str = Field(default="temp_mean")
    temp_max_column: str = Field(default="temp_max")
    temp_min_column: str = Field(default="temp_min")
    humidity_column: str = Field(default="humidity")
    precipitation_column: str = Field(default="precipitation")
    wind_speed_column: str = Field(default="wind_speed")

    # Heatwave thresholds
    heatwave_temp_threshold: float = Field(default=28.0)
    heatwave_duration_days: int = Field(default=3)

    # Missing-data strategy for weather features
    missing_weather_strategy: str = Field(default="mean")

    # Logging
    log_level: str = Field(default="INFO")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = ["DEBUG", "INFO", "WARNING", "ERROR"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return v

    # ── Computed paths ────────────────────────────────────────────────────────

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def model_path(self) -> Path:
        return self.base_dir / self.model_dir

    @property
    def data_path(self) -> Path:
        return self.base_dir / self.data_dir

    @property
    def reports_path(self) -> Path:
        return self.base_dir / self.reports_dir

    @property
    def raw_data_path(self) -> Path:
        return self.data_path / "raw"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    # Alias used by ModelTrainer
    @property
    def models_path(self) -> Path:
        return self.model_path


settings = Settings()
