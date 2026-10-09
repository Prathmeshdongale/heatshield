"""Tests for GET /api/v1/weather"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_weather_200():
    r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.status_code == 200


def test_weather_default_7_days():
    r = client.get("/api/v1/weather?hospital_id=H001")
    body = r.json()
    assert len(body["data"]["observations"]) == 7


def test_weather_custom_days():
    r = client.get("/api/v1/weather?hospital_id=H001&days=3")
    assert len(r.json()["data"]["observations"]) == 3


def test_weather_observation_fields():
    r = client.get("/api/v1/weather?hospital_id=H001&days=1")
    obs = r.json()["data"]["observations"][0]
    for field in ("observation_date", "temperature_max_c", "temperature_min_c",
                  "humidity_pct", "heat_index_c", "condition"):
        assert field in obs, f"Missing field: {field}"


def test_weather_demo_label():
    r = client.get("/api/v1/weather?hospital_id=H001")
    assert r.json()["status"]["data_source"] == "demo"


def test_weather_unknown_hospital_404():
    r = client.get("/api/v1/weather?hospital_id=ZZZZ")
    assert r.status_code == 404


def test_weather_days_over_limit_422():
    r = client.get("/api/v1/weather?hospital_id=H001&days=99")
    assert r.status_code == 422
