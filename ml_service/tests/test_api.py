"""Tests for ML Service API endpoints."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

_VALID_FORECAST = {
    "date": "2024-08-15",
    "location": "SYN001",
    "temperature": 32.0,
    "humidity": 60.0,
    "weather_condition": "hot",
}

_INVALID_TEMP = {**_VALID_FORECAST, "temperature": 200.0}


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_model_status_returns_200_or_503():
    r = client.get("/api/v1/model/status")
    assert r.status_code in (200, 503)


def test_forecast_no_model_returns_503_or_200():
    """Accepts 200 (model loaded) or 503 (model absent)."""
    r = client.post("/api/v1/forecast", json=_VALID_FORECAST)
    assert r.status_code in (200, 503)


def test_forecast_invalid_temperature_422():
    r = client.post("/api/v1/forecast", json=_INVALID_TEMP)
    assert r.status_code == 422


def test_forecast_invalid_humidity_422():
    payload = {**_VALID_FORECAST, "humidity": 150.0}
    r = client.post("/api/v1/forecast", json=payload)
    assert r.status_code == 422


def test_weather_endpoint_returns_200_or_500():
    r = client.post("/api/v1/weather", json={
        "location": "London",
        "start_date": "2024-08-01T00:00:00",
        "end_date":   "2024-08-10T00:00:00",
        "include_forecast": False,
    })
    assert r.status_code in (200, 500)
