"""
test_db_schema.py — validates DB assumptions without a live connection.

These tests confirm:
  1. Repositories raise RuntimeError when DB is unavailable (no silent fallback).
  2. Repository output shape when DB IS available matches Pydantic schemas.
  3. mock_data.py (used only as seed reference) is internally consistent.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


# ── Repositories raise when DB is None ───────────────────────────────────────

class TestRepositoriesRequireDB:
    def test_fetch_all_hospitals_raises_without_db(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_all_hospitals
            with pytest.raises(RuntimeError):
                fetch_all_hospitals()

    def test_fetch_hospital_by_id_raises_without_db(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_hospital_by_id
            with pytest.raises(RuntimeError):
                fetch_hospital_by_id("H001")

    def test_fetch_weather_raises_without_db(self):
        with patch("app.repositories.weather_repository.get_supabase", return_value=None):
            from app.repositories.weather_repository import fetch_weather
            with pytest.raises(RuntimeError):
                fetch_weather("H001", 3)

    def test_fetch_forecast_raises_without_db(self):
        with patch("app.repositories.forecast_repository.get_supabase", return_value=None):
            from app.repositories.forecast_repository import fetch_forecast
            with pytest.raises(RuntimeError):
                fetch_forecast("H001", 7)

    def test_fetch_latest_metrics_raises_without_db(self):
        with patch("app.repositories.metrics_repository.get_supabase", return_value=None):
            from app.repositories.metrics_repository import fetch_latest_metrics
            with pytest.raises(RuntimeError):
                fetch_latest_metrics()


# ── Repository output shape when DB is available ─────────────────────────────

today = date.today()

def _mock_hospital():
    return {
        "hospital_id": "H001", "name": "City General [DEMO]", "region": "Greater London",
        "address": "1 Demo Rd", "latitude": 51.5, "longitude": -0.1,
        "contact_email": "ops@demo.nhs", "capacity_total": 300, "data_status": "demo",
    }

def _mock_capacity():
    return {"hospital_id": "H001", "recorded_date": str(today), "capacity_total": 300,
            "capacity_available": 72, "occupancy_pct": 76.0, "risk_status": "amber"}

def _mock_weather_obs(n=7):
    return [{"observation_date": str(today - timedelta(days=i)),
             "temperature_max_c": 34.0, "temperature_min_c": 22.0,
             "humidity_pct": 65.0, "heat_index_c": 38.0, "condition": "Heatwave"}
            for i in range(n)]

def _mock_forecast_rows(n=7):
    return [{"forecast_date": str(today + timedelta(days=i+1)),
             "predicted_admissions": 42.5, "confidence_lower": 36.1,
             "confidence_upper": 48.9, "risk_status": "amber",
             "model_version": "v1.2.0-demo", "generated_at": "2026-10-09T08:00:00+00:00"}
            for i in range(n)]


class TestHospitalRepositoryShape:
    def test_list_required_fields(self):
        m = MagicMock()
        def sel(table, **kw):
            if table == "hospitals": return [_mock_hospital()]
            if table == "hospital_capacity": return [_mock_capacity()]
            return []
        m.select.side_effect = sel
        with patch("app.repositories.hospital_repository.get_supabase", return_value=m):
            from app.repositories.hospital_repository import fetch_all_hospitals
            hospitals = fetch_all_hospitals()
        assert len(hospitals) == 1
        h = hospitals[0]
        for field in ("hospital_id", "name", "region", "capacity_total",
                      "capacity_available", "occupancy_pct", "risk_status"):
            assert field in h, f"Missing field '{field}'"

    def test_detail_by_id(self):
        m = MagicMock()
        def sel(table, **kw):
            single = kw.get("single", False)
            if table == "hospitals": return _mock_hospital() if single else [_mock_hospital()]
            if table == "hospital_capacity": return [_mock_capacity()]
            return []
        m.select.side_effect = sel
        with patch("app.repositories.hospital_repository.get_supabase", return_value=m):
            from app.repositories.hospital_repository import fetch_hospital_by_id
            h = fetch_hospital_by_id("H001")
        assert h is not None
        assert h["hospital_id"] == "H001"

    def test_missing_id_returns_none(self):
        m = MagicMock()
        m.select.return_value = None
        with patch("app.repositories.hospital_repository.get_supabase", return_value=m):
            from app.repositories.hospital_repository import fetch_hospital_by_id
            assert fetch_hospital_by_id("ZZZZ") is None


class TestWeatherRepositoryShape:
    def test_correct_day_count(self):
        m = MagicMock()
        m.select.return_value = _mock_weather_obs(5)
        with patch("app.repositories.weather_repository.get_supabase", return_value=m):
            from app.repositories.weather_repository import fetch_weather
            result = fetch_weather("H001", 5)
        assert len(result["observations"]) == 5

    def test_observation_fields(self):
        m = MagicMock()
        m.select.return_value = _mock_weather_obs(1)
        with patch("app.repositories.weather_repository.get_supabase", return_value=m):
            from app.repositories.weather_repository import fetch_weather
            obs = fetch_weather("H001", 1)["observations"][0]
        for field in ("observation_date", "temperature_max_c", "temperature_min_c",
                      "humidity_pct", "heat_index_c", "condition"):
            assert field in obs


class TestForecastRepositoryShape:
    def test_correct_point_count(self):
        m = MagicMock()
        m.select.return_value = _mock_forecast_rows(7)
        with patch("app.repositories.forecast_repository.get_supabase", return_value=m):
            from app.repositories.forecast_repository import fetch_forecast
            result = fetch_forecast("H001", 7)
        assert len(result["points"]) == 7

    def test_forecast_point_fields(self):
        m = MagicMock()
        m.select.return_value = _mock_forecast_rows(1)
        with patch("app.repositories.forecast_repository.get_supabase", return_value=m):
            from app.repositories.forecast_repository import fetch_forecast
            point = fetch_forecast("H001", 1)["points"][0]
        for field in ("forecast_date", "predicted_admissions",
                      "confidence_lower", "confidence_upper", "risk_status"):
            assert field in point

    def test_confidence_bounds_valid(self):
        m = MagicMock()
        m.select.return_value = _mock_forecast_rows(7)
        with patch("app.repositories.forecast_repository.get_supabase", return_value=m):
            from app.repositories.forecast_repository import fetch_forecast
            for pt in fetch_forecast("H001", 7)["points"]:
                assert pt["confidence_lower"] <= pt["predicted_admissions"] <= pt["confidence_upper"]


# ── mock_data.py internal consistency (still used as seed reference) ──────────

class TestMockDataConsistency:
    def test_all_hospitals_have_valid_risk_status(self):
        from app.mock_data import HOSPITALS
        valid = {"green", "amber", "red", "critical"}
        for hid, h in HOSPITALS.items():
            assert h["risk_status"] in valid

    def test_occupancy_matches_capacity(self):
        from app.mock_data import HOSPITALS
        for hid, h in HOSPITALS.items():
            expected = round(
                (h["capacity_total"] - h["capacity_available"]) / h["capacity_total"] * 100, 1
            )
            assert abs(h["occupancy_pct"] - expected) < 1.0

    def test_demo_label_in_name(self):
        from app.mock_data import HOSPITALS
        for hid, h in HOSPITALS.items():
            assert "[DEMO]" in h["name"], f"Hospital '{hid}' name must contain [DEMO]"
