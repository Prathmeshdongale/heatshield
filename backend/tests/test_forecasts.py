"""Tests for GET /api/v1/forecasts"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_forecast_default_days_200():
    r = client.get("/api/v1/forecasts?hospital_id=H001")
    assert r.status_code == 200


def test_forecast_returns_correct_day_count():
    r = client.get("/api/v1/forecasts?hospital_id=H001&days=5")
    body = r.json()
    assert len(body["data"]["points"]) == 5


def test_forecast_default_is_7_days():
    r = client.get("/api/v1/forecasts?hospital_id=H001")
    body = r.json()
    assert body["data"]["days_requested"] == 7
    assert len(body["data"]["points"]) == 7


def test_forecast_point_fields():
    r = client.get("/api/v1/forecasts?hospital_id=H001&days=1")
    point = r.json()["data"]["points"][0]
    for field in ("forecast_date", "predicted_admissions",
                  "confidence_lower", "confidence_upper", "risk_status"):
        assert field in point, f"Missing field: {field}"


def test_forecast_demo_label():
    r = client.get("/api/v1/forecasts?hospital_id=H001")
    assert r.json()["status"]["data_source"] == "demo"


def test_forecast_unknown_hospital_404():
    r = client.get("/api/v1/forecasts?hospital_id=ZZZZ")
    assert r.status_code == 404


def test_forecast_days_zero_422():
    r = client.get("/api/v1/forecasts?hospital_id=H001&days=0")
    assert r.status_code == 422


def test_forecast_days_over_limit_422():
    r = client.get("/api/v1/forecasts?hospital_id=H001&days=15")
    assert r.status_code == 422


def test_forecast_missing_hospital_id_422():
    r = client.get("/api/v1/forecasts")
    assert r.status_code == 422
