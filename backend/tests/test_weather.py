"""Tests for GET /api/v1/weather"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_OBS = {
    "observation_date": "2026-10-09", "temperature_max_c": 34.2,
    "temperature_min_c": 23.7, "humidity_pct": 65.0,
    "heat_index_c": 38.0, "condition": "Heatwave",
}


def _patch_db(n_rows=7):
    m = MagicMock()
    m.select.return_value = [
        dict(_OBS, observation_date=f"2026-10-0{i+1}") for i in range(n_rows)
    ]
    return patch("app.repositories.weather_repository.get_supabase", return_value=m)


def test_weather_200():
    with _patch_db():
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.status_code == 200


def test_weather_default_7_days():
    with _patch_db(7):
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert len(r.json()["data"]["observations"]) == 7


def test_weather_custom_days():
    with _patch_db(3):
        r = client.get("/api/v1/weather?hospital_id=H001&days=3")
    assert len(r.json()["data"]["observations"]) == 3


def test_weather_observation_fields():
    with _patch_db(1):
        r = client.get("/api/v1/weather?hospital_id=H001&days=1")
    obs = r.json()["data"]["observations"][0]
    for field in ("observation_date", "temperature_max_c", "temperature_min_c",
                  "humidity_pct", "heat_index_c", "condition"):
        assert field in obs, f"Missing field: {field}"


def test_weather_returns_live_label():
    with _patch_db():
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.json()["status"]["data_source"] == "live"


def test_weather_503_when_db_down():
    with patch("app.repositories.weather_repository.get_supabase", return_value=None):
        r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.status_code == 503


def test_weather_days_over_limit_422():
    r = client.get("/api/v1/weather?hospital_id=H001&days=99")
    assert r.status_code == 422
