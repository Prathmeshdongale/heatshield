"""
weather_service.py — live temperature and humidity from Open-Meteo.

Hospital coordinates come from the database when available; otherwise the
known NHS-region defaults (London / Manchester) are used.
"""

import logging

from app.config import get_settings
from app.integrations.open_meteo import fetch_daily_weather, map_observations
from app.repositories.hospital_repository import fetch_hospital_by_id

logger = logging.getLogger(__name__)

_MIN_DAYS = 1
_MAX_DAYS = 92

# Fallback coordinates used when the hospital row is not in the database.
HOSPITAL_COORDS: dict[str, tuple[float, float]] = {
    "H001": (51.5074, -0.1278),  # Greater London
    "H002": (51.4995, -0.1157),  # Greater London
    "H003": (53.4808, -2.2426),  # Greater Manchester
}
DEFAULT_COORDS = (51.5074, -0.1278)


def _hospital_coords(hospital_id: str) -> tuple[float, float]:
    try:
        hospital = fetch_hospital_by_id(hospital_id)
        if hospital and hospital.get("latitude") is not None and hospital.get("longitude") is not None:
            return float(hospital["latitude"]), float(hospital["longitude"])
    except Exception as exc:
        logger.debug("Hospital coordinates unavailable from DB for %s: %s", hospital_id, exc)
    return HOSPITAL_COORDS.get(hospital_id.upper(), DEFAULT_COORDS)


def get_weather(hospital_id: str, days: int) -> tuple[dict, str]:
    """
    Returns (weather_response, 'live').
    Raises ValueError if days is out of range.
    Raises RuntimeError if Open-Meteo is unreachable.
    """
    if not (_MIN_DAYS <= days <= _MAX_DAYS):
        raise ValueError(f"days must be in [{_MIN_DAYS}, {_MAX_DAYS}], got {days}")

    hid = hospital_id.upper()
    lat, lon = _hospital_coords(hid)
    settings = get_settings()
    try:
        payload = fetch_daily_weather(
            latitude=lat,
            longitude=lon,
            days=days,
            timezone=settings.weather_timezone,
            base_url=settings.open_meteo_url,
        )
        observations = map_observations(payload, days)
    except Exception as exc:
        logger.exception("Open-Meteo request failed for %s", hid)
        raise RuntimeError("Weather provider unavailable") from exc

    return {
        "hospital_id": hid,
        "days_requested": days,
        "observations": observations,
    }, "live"
