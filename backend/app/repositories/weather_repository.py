"""
weather_repository.py — Supabase queries for weather_daily.
No demo fallback — returns real DB data or raises on failure.
"""

import logging
from app.integrations.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def fetch_weather(hospital_id: str, days: int) -> dict:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client not configured")

    hid = hospital_id.upper()
    rows = client.select(
        "weather_daily",
        columns="observation_date,temperature_max_c,temperature_min_c,humidity_pct,heat_index_c,condition",
        filters={"hospital_id": hid},
        order="observation_date",
        desc=True,
        limit=days,
    )
    observations = sorted(rows, key=lambda r: r["observation_date"])
    return {
        "hospital_id":    hid,
        "days_requested": days,
        "observations":   observations,
    }
