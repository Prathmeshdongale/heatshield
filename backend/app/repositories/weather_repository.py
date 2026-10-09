"""
weather_repository.py — Supabase queries for weather_daily table.

Falls back to mock_data.get_demo_weather() if DB is unavailable.
"""

import logging
from app.integrations.supabase_client import get_supabase
from app.mock_data import get_demo_weather

logger = logging.getLogger(__name__)


def fetch_weather(hospital_id: str, days: int) -> dict:
    """
    Returns up to `days` most-recent daily weather observations for a hospital.
    Falls back to demo data on DB unavailability or error.
    """
    client = get_supabase()
    hid = hospital_id.upper()

    if client is None:
        return get_demo_weather(hid, days)

    try:
        resp = (
            client.table("weather_daily")
            .select(
                "observation_date, temperature_max_c, temperature_min_c, "
                "humidity_pct, heat_index_c, condition"
            )
            .eq("hospital_id", hid)       # parameterised
            .order("observation_date", desc=True)
            .limit(days)
            .execute()
        )

        # Return in ascending date order so the frontend charts left-to-right
        observations = sorted(resp.data, key=lambda r: r["observation_date"])

        return {
            "hospital_id": hid,
            "days_requested": days,
            "observations": observations,
        }

    except Exception as exc:
        logger.error("fetch_weather DB error (%s): %s — falling back to demo", hid, exc)
        return get_demo_weather(hid, days)
