"""
config.py — application settings loaded from environment variables / .env file.
All other modules import `get_settings()` rather than reading os.environ directly.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------------------------------------------
    # App
    # -----------------------------------------------------------------
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me"

    # -----------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------
    # Stored as a comma-separated string in .env, parsed to a list here.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # -----------------------------------------------------------------
    # Supabase  — publishable/anon key only, never the service-role key
    # -----------------------------------------------------------------
    supabase_url: str = ""
    supabase_publishable_key: str = ""

    # -----------------------------------------------------------------
    # Demo mode
    # Set DEMO_MODE=true to serve synthetic data even when DB / ML are
    # available. Useful for presentations. Always false in production.
    # -----------------------------------------------------------------
    demo_mode: bool = True

    # -----------------------------------------------------------------
    # ML
    # -----------------------------------------------------------------
    ml_model_path: str = "../ml/artifacts/model.joblib"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once at startup)."""
    return Settings()
