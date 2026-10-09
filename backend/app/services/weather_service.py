"""
weather_service.py — business logic for weather data.

Responsibilities:
  - Fetch weather observations from the repository.
  - In demo mode, return mock weather data.
  - Validate that days is within acceptable range (caller should enforce
    this via query-param constraints, but we double-check).
"""

import logging
from app.config import get_settings
from app.repositories.weather_repository import fetch_weather
from app.mock_data import get_demo_weather, HOSPITALS

logger = logging.getLogger(__name__)

_MAX_DAYS = 14
_MIN_DAYS = 1


def get_weather(hospital_id: str, days: int) -> tuple[dict, str]:
    """
    Returns (weather_response, data_source).
    data_source is 'demo' or 'live'.
    Raises ValueError if days is out of range.
    Raises KeyError if hospital_id is not found (both demo and live mode).
    """
    if not (_MIN_DAYS <= days <= _MAX_DAYS):
        raise ValueError(f"days must be in [{_MIN_DAYS}, {_MAX_DAYS}], got {days}")

    settings = get_settings()
    hid = hospital_id.upper()

    if settings.demo_mode:
        if hid not in HOSPITALS:
            raise KeyError(f"Hospital '{hospital_id}' not found")
        return get_demo_weather(hid, days), "demo"

    # Live mode — repository falls back gracefully if DB is unavailable
    # but we still gate on hospital existence
    if hid not in HOSPITALS:
        raise KeyError(f"Hospital '{hospital_id}' not found")

    weather = fetch_weather(hid, days)
    data_source = "demo" if not settings.supabase_url else "live"
    return weather, data_source
