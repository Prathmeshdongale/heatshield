"""
open_meteo.py — client for the Open-Meteo forecast API.

Open-Meteo is an open-source weather API (no API key). HeatShield uses it
for daily temperature, humidity, apparent temperature, and WMO weather codes.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CONDITIONS = {
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

DAILY_VARS = (
    "temperature_2m_max,"
    "temperature_2m_min,"
    "relative_humidity_2m_mean,"
    "apparent_temperature_max,"
    "weather_code"
)


def heat_index_c(temp_c: float, humidity_pct: float) -> float:
    """NWS Rothfusz heat index, returned in °C."""
    t = temp_c * 9 / 5 + 32
    rh = humidity_pct
    hi_f = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * rh
        - 0.22475541 * t * rh
        - 0.00683783 * t * t
        - 0.05481717 * rh * rh
        + 0.00122874 * t * t * rh
        + 0.00085282 * t * rh * rh
        - 0.00000199 * t * t * rh * rh
    )
    return round((hi_f - 32) * 5 / 9, 1)


def condition_label(weather_code: int | None, temp_max_c: float) -> str:
    name = WMO_CONDITIONS.get(int(weather_code) if weather_code is not None else -1, "Unknown")
    if temp_max_c >= 35:
        return "Heatwave"
    if temp_max_c >= 28:
        return f"Hot — {name}"
    return name


def fetch_daily_weather(
    latitude: float,
    longitude: float,
    days: int,
    timezone: str = "Europe/London",
    base_url: str = OPEN_METEO_URL,
    timeout: float = 10.0,
) -> dict:
    """Fetch daily observations for the last `days` days (including today)."""
    past_days = max(int(days) - 1, 0)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": DAILY_VARS,
        "timezone": timezone,
        "past_days": past_days,
        "forecast_days": 1,
    }
    logger.info(
        "Open-Meteo request lat=%.4f lon=%.4f days=%s timezone=%s",
        latitude,
        longitude,
        days,
        timezone,
    )
    with httpx.Client(timeout=timeout) as client:
        response = client.get(base_url, params=params)
        response.raise_for_status()
        return response.json()


def map_observations(payload: dict, days: int) -> list[dict]:
    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    humidity = daily.get("relative_humidity_2m_mean") or []
    apparent = daily.get("apparent_temperature_max") or []
    codes = daily.get("weather_code") or []

    rows: list[dict] = []
    for i, date_str in enumerate(times):
        if i >= len(tmax) or tmax[i] is None:
            continue
        t_max = float(tmax[i])
        t_min = float(tmin[i]) if i < len(tmin) and tmin[i] is not None else t_max - 10.0
        rh = float(humidity[i]) if i < len(humidity) and humidity[i] is not None else 0.0
        rh = max(0.0, min(100.0, rh))
        if i < len(apparent) and apparent[i] is not None:
            heat = float(apparent[i])
        else:
            heat = heat_index_c(t_max, rh)
        code = int(codes[i]) if i < len(codes) and codes[i] is not None else None
        rows.append(
            {
                "observation_date": date_str,
                "temperature_max_c": round(t_max, 1),
                "temperature_min_c": round(t_min, 1),
                "humidity_pct": round(rh, 1),
                "heat_index_c": round(heat, 1),
                "condition": condition_label(code, t_max),
            }
        )
    return rows[-days:]
