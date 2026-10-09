"""Tests for GET /api/v1/forecasts"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

today = date.today()

_HOSPITAL_ROW = {
    "hospital_id": "H001", "name": "City General [TEST]", "region": "Greater London",
    "address": "1 Test Rd", "latitude": 51.5, "longitude": -0.1,
    "contact_email": "test@test.nhs", "capacity_total": 300, "data_status": "demo",
    "capacity_available": 72, "occupancy_pct": 76.0, "risk_status": "amber",
}


def _forecast_rows(n=7):
    return [
        {"forecast_date": str(today + timedelta(days=i + 1)),
         "predicted_admissions": 42.5 + i, "confidence_lower": 36.1 + i,
         "confidence_upper": 48.9 + i, "risk_status": "amber",
         "model_version": "v1.2.0-demo", "generated_at": "2026-10-09T08:00:00+00:00"}
        for i in range(n)
    ]


def _patch_db(n_forecast=7, hospital_missing=False):
    hm = MagicMock()
    def hm_select(table, **kwargs):
        single = kwargs.get("single", False)
        if table == "hospitals":
            return None if hospital_missing else (_HOSPITAL_ROW if single else [_HOSPITAL_ROW])
        if table == "hospital_capacity":
            return []
        return []
    hm.select.side_effect = hm_select

    fm = MagicMock()
    fm.select.return_value = _forecast_rows(n_forecast)

    return (
        patch("app.repositories.hospital_repository.get_supabase", return_value=hm),
        patch("app.repositories.forecast_repository.get_supabase", return_value=fm),
    )


def test_forecast_default_days_200():
    hp, fp = _patch_db(7)
    with hp, fp:
        r = client.get("/api/v1/forecasts?hospital_id=H001")
    assert r.status_code == 200


def test_forecast_returns_correct_day_count():
    hp, fp = _patch_db(5)
    with hp, fp:
        r = client.get("/api/v1/forecasts?hospital_id=H001&days=5")
    assert len(r.json()["data"]["points"]) == 5


def test_forecast_default_is_7_days():
    hp, fp = _patch_db(7)
    with hp, fp:
        r = client.get("/api/v1/forecasts?hospital_id=H001")
    body = r.json()
    assert body["data"]["days_requested"] == 7
    assert len(body["data"]["points"]) == 7


def test_forecast_point_fields():
    hp, fp = _patch_db(1)
    with hp, fp:
        r = client.get("/api/v1/forecasts?hospital_id=H001&days=1")
    point = r.json()["data"]["points"][0]
    for field in ("forecast_date", "predicted_admissions",
                  "confidence_lower", "confidence_upper", "risk_status"):
        assert field in point, f"Missing field: {field}"


def test_forecast_returns_live_label():
    hp, fp = _patch_db(7)
    with hp, fp, \
         patch("app.services.forecast_service.is_db_available", return_value=True):
        r = client.get("/api/v1/forecasts?hospital_id=H001")
    assert r.json()["status"]["data_source"] == "live"


def test_forecast_unknown_hospital_404():
    hp, fp = _patch_db(hospital_missing=True)
    with hp, fp:
        r = client.get("/api/v1/forecasts?hospital_id=ZZZZ")
    assert r.status_code == 404


def test_forecast_503_when_db_down():
    with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
        r = client.get("/api/v1/forecasts?hospital_id=H001")
    assert r.status_code == 503


def test_forecast_days_zero_422():
    r = client.get("/api/v1/forecasts?hospital_id=H001&days=0")
    assert r.status_code == 422


def test_forecast_days_over_limit_422():
    r = client.get("/api/v1/forecasts?hospital_id=H001&days=15")
    assert r.status_code == 422


def test_forecast_missing_hospital_id_422():
    r = client.get("/api/v1/forecasts")
    assert r.status_code == 422
