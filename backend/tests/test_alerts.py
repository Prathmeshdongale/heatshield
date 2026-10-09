"""Tests for GET /api/v1/alerts"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_alerts_all_200():
    r = client.get("/api/v1/alerts")
    assert r.status_code == 200


def test_alerts_returns_list():
    r = client.get("/api/v1/alerts")
    body = r.json()
    assert isinstance(body["data"], list)


def test_alerts_filter_by_hospital():
    r = client.get("/api/v1/alerts?hospital_id=H002")
    body = r.json()
    for alert in body["data"]:
        assert alert["hospital_id"] == "H002"


def test_alerts_filter_returns_empty_for_unknown():
    r = client.get("/api/v1/alerts?hospital_id=ZZZZ")
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_alerts_meta_count_matches():
    r = client.get("/api/v1/alerts")
    body = r.json()
    assert body["meta"]["count"] == len(body["data"])


def test_alerts_demo_label():
    r = client.get("/api/v1/alerts")
    assert r.json()["status"]["data_source"] == "demo"


def test_alert_fields():
    r = client.get("/api/v1/alerts")
    alerts = r.json()["data"]
    if alerts:
        for field in ("alert_id", "hospital_id", "severity", "message",
                      "triggered_at", "forecast_date", "resolved"):
            assert field in alerts[0], f"Missing field: {field}"
