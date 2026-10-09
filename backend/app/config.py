"""
config.py — application settings loaded from environment variables / .env file.
"""

import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Backend package root (the directory containing this file's parent)
_BACKEND_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    # App
    app_env:    str = "development"
    app_host:   str = "0.0.0.0"
    app_port:   int = 8000
    secret_key: str = "change-me"

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # Supabase
    supabase_url:             str = ""
    supabase_publishable_key: str = ""

    # Open-Meteo (open-source weather API — no key required)
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timezone: str = "Europe/London"

    # Demo mode
    demo_mode: bool = False

    # ML model path — relative paths resolved from backend/ directory
    ml_model_path: str = "ml/artifacts/model.joblib"

    @property
    def ml_model_path_abs(self) -> str:
        """Return absolute path to the model artifact."""
        p = Path(self.ml_model_path)
        if p.is_absolute():
            return str(p)
        return str(_BACKEND_DIR / p)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
