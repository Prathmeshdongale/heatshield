"""
weather_service.py — weather data from the real database.
No demo fallback — all data comes from Supabase.
"""

import logging
from app.repositories.weather_repository import fetch_weather

logger = logging.getLogger(__name__)

_MAX_DAYS = 14
_MIN_DAYS = 1


def get_weather(hospital_id: str, days: int) -> tuple[dict, str]:
    """
    Returns (weather_response, 'live').
    Raises ValueError if days is out of range.
    Raises RuntimeError if DB is unreachable.
    """
    if not (_MIN_DAYS <= days <= _MAX_DAYS):
        raise ValueError(f"days must be in [{_MIN_DAYS}, {_MAX_DAYS}], got {days}")

    weather = fetch_weather(hospital_id.upper(), days)
    return weather, "live"
