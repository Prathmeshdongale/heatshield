"""Tests for GET /api/v1/alerts"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

today = date.today()

_HOSPITAL_H002 = {
    "hospital_id": "H002", "name": "Riverside [TEST]", "region": "Greater London",
    "address": "22 River Lane", "latitude": 51.5, "longitude": -0.1,
    "contact_email": "test@test.nhs", "capacity_total": 180, "data_status": "demo",
    "capacity_available": 15, "occupancy_pct": 91.67, "risk_status": "red",
}

_FORECAST_ROWS = [
    {"forecast_date": str(today + timedelta(days=1)), "predicted_admissions": 27.0,
     "confidence_lower": 23.0, "confidence_upper": 31.1, "risk_status": "red",
     "model_version": "v1.2.0-demo", "generated_at": "2026-10-09T08:00:00+00:00"},
    {"forecast_date": str(today + timedelta(days=2)), "predicted_admissions": 29.4,
     "confidence_lower": 25.0, "confidence_upper": 33.8, "risk_status": "critical",
     "model_version": "v1.2.0-demo", "generated_at": "2026-10-09T08:00:00+00:00"},
    {"forecast_date": str(today + timedelta(days=3)), "predicted_admissions": 32.5,
     "confidence_lower": 27.6, "confidence_upper": 37.4, "risk_status": "green",
     "model_version": "v1.2.0-demo", "generated_at": "2026-10-09T08:00:00+00:00"},
]


def _patch_db():
    """Patch both hospital and forecast repos."""
    hm = MagicMock()
    def hm_select(table, **kwargs):
        single = kwargs.get("single", False)
        if table == "hospitals":
            return _HOSPITAL_H002 if single else [_HOSPITAL_H002]
        if table == "hospital_capacity":
            return []
        return []
    hm.select.side_effect = hm_select

    fm = MagicMock()
    fm.select.return_value = _FORECAST_ROWS

    return (
        patch("app.repositories.hospital_repository.get_supabase", return_value=hm),
        patch("app.repositories.forecast_repository.get_supabase", return_value=fm),
    )


def test_alerts_all_200():
    hp, fp = _patch_db()
    with hp, fp:
        r = client.get("/api/v1/alerts")
    assert r.status_code == 200


def test_alerts_returns_list():
    hp, fp = _patch_db()
    with hp, fp:
        r = client.get("/api/v1/alerts")
    assert isinstance(r.json()["data"], list)


def test_alerts_only_red_and_critical():
    hp, fp = _patch_db()
    with hp, fp:
        r = client.get("/api/v1/alerts")
    alerts = r.json()["data"]
    assert len(alerts) == 2  # red + critical; green excluded


def test_alerts_meta_count_matches():
    hp, fp = _patch_db()
    with hp, fp:
        r = client.get("/api/v1/alerts")
    body = r.json()
    assert body["meta"]["count"] == len(body["data"])


def test_alerts_returns_live_label():
    hp, fp = _patch_db()
    with hp, fp:
        r = client.get("/api/v1/alerts")
    assert r.json()["status"]["data_source"] == "live"


def test_alerts_503_when_db_down():
    with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
        r = client.get("/api/v1/alerts")
    assert r.status_code == 503


def test_alert_fields():
    hp, fp = _patch_db()
    with hp, fp:
        r = client.get("/api/v1/alerts")
    alerts = r.json()["data"]
    if alerts:
        for field in ("alert_id", "hospital_id", "severity", "message",
                      "triggered_at", "forecast_date", "resolved"):
            assert field in alerts[0], f"Missing field: {field}"
