"""Tests for GET /api/v1/weather (Open-Meteo-backed)."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.integrations.open_meteo import map_observations, condition_label, heat_index_c

client = TestClient(app)

_SAMPLE_PAYLOAD = {
    "daily": {
        "time": ["2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06",
                 "2026-10-07", "2026-10-08", "2026-10-09"],
        "temperature_2m_max": [21.3, 17.9, 15.1, 20.0, 28.4, 36.2, 22.0],
        "temperature_2m_min": [13.6, 10.2, 7.9, 11.1, 16.0, 22.0, 12.0],
        "relative_humidity_2m_mean": [78, 86, 64, 74, 55, 40, 70],
        "apparent_temperature_max": [21.3, 18.6, 11.8, 17.6, 29.1, 38.0, 22.5],
        "weather_code": [3, 63, 51, 53, 1, 0, 2],
    }
}


def _patch_meteo(payload=None, days=None):
    data = payload if payload is not None else _SAMPLE_PAYLOAD
    if days is not None:
        data = {"daily": {key: values[:days] for key, values in _SAMPLE_PAYLOAD["daily"].items()}}
    return patch("app.services.weather_service.fetch_daily_weather", return_value=data)


def test_weather_200():
    with _patch_meteo():
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.status_code == 200


def test_weather_default_7_days():
    with _patch_meteo():
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert len(r.json()["data"]["observations"]) == 7


def test_weather_custom_days():
    with _patch_meteo(days=3):
        r = client.get("/api/v1/weather?hospital_id=H001&days=3")
    assert r.status_code == 200
    assert len(r.json()["data"]["observations"]) == 3


def test_weather_observation_fields():
    with _patch_meteo(days=1):
        r = client.get("/api/v1/weather?hospital_id=H001&days=1")
    obs = r.json()["data"]["observations"][0]
    for field in ("observation_date", "temperature_max_c", "temperature_min_c",
                  "humidity_pct", "heat_index_c", "condition"):
        assert field in obs, f"Missing field: {field}"


def test_weather_returns_live_open_meteo_label():
    with _patch_meteo():
        r = client.get("/api/v1/weather?hospital_id=H001")
    status = r.json()["status"]
    assert status["data_source"] == "live"
    assert "Open-Meteo" in status["note"]


def test_weather_503_when_provider_down():
    with patch("app.services.weather_service.fetch_daily_weather", side_effect=RuntimeError("timeout")):
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "WEATHER_UNAVAILABLE"


def test_weather_days_over_limit_422():
    r = client.get("/api/v1/weather?hospital_id=H001&days=99")
    assert r.status_code == 422


def test_map_observations_humidity_and_heat():
    rows = map_observations(_SAMPLE_PAYLOAD, 7)
    assert rows[0]["humidity_pct"] == 78.0
    assert rows[-2]["condition"] == "Heatwave"  # 36.2 °C
    assert rows[-3]["condition"].startswith("Hot")  # 28.4 °C


def test_condition_and_heat_index_helpers():
    assert condition_label(0, 20) == "Clear sky"
    assert heat_index_c(30, 70) > 30
