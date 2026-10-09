"""
test_db_schema.py — validates database assumptions without a live DB connection.

These tests confirm:
  1. The repository layer falls back to demo data when the DB is unavailable.
  2. Repository output matches the shape expected by Pydantic schemas.
  3. The mock data used as fallback is internally consistent.

No live Supabase connection is required — the tests patch is_db_available()
to simulate an unavailable database.
"""

import pytest
from unittest.mock import patch
from datetime import date


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db_unavailable():
    """Patch target that simulates no DB connection."""
    return None


# ── hospital_repository ───────────────────────────────────────────────────────

class TestHospitalRepositoryFallback:
    def test_fetch_all_hospitals_returns_list(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_all_hospitals
            result = fetch_all_hospitals()
            assert isinstance(result, list)
            assert len(result) > 0

    def test_fetch_all_hospitals_required_fields(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_all_hospitals
            for hospital in fetch_all_hospitals():
                for field in ("hospital_id", "name", "region", "capacity_total",
                              "capacity_available", "occupancy_pct", "risk_status"):
                    assert field in hospital, f"Missing field '{field}' in {hospital}"

    def test_fetch_hospital_by_id_known(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_hospital_by_id
            result = fetch_hospital_by_id("H001")
            assert result is not None
            assert result["hospital_id"] == "H001"

    def test_fetch_hospital_by_id_unknown_returns_none(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_hospital_by_id
            result = fetch_hospital_by_id("ZZZZ")
            assert result is None

    def test_fetch_hospital_case_insensitive(self):
        with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
            from app.repositories.hospital_repository import fetch_hospital_by_id
            assert fetch_hospital_by_id("h001") is not None


# ── weather_repository ────────────────────────────────────────────────────────

class TestWeatherRepositoryFallback:
    def test_returns_correct_day_count(self):
        with patch("app.repositories.weather_repository.get_supabase", return_value=None):
            from app.repositories.weather_repository import fetch_weather
            result = fetch_weather("H001", 5)
            assert len(result["observations"]) == 5

    def test_observation_fields(self):
        with patch("app.repositories.weather_repository.get_supabase", return_value=None):
            from app.repositories.weather_repository import fetch_weather
            obs = fetch_weather("H001", 1)["observations"][0]
            for field in ("observation_date", "temperature_max_c", "temperature_min_c",
                          "humidity_pct", "heat_index_c", "condition"):
                assert field in obs, f"Missing field '{field}'"

    def test_hospital_id_preserved(self):
        with patch("app.repositories.weather_repository.get_supabase", return_value=None):
            from app.repositories.weather_repository import fetch_weather
            result = fetch_weather("H002", 3)
            assert result["hospital_id"] == "H002"


# ── forecast_repository ───────────────────────────────────────────────────────

class TestForecastRepositoryFallback:
    def test_returns_correct_point_count(self):
        with patch("app.repositories.forecast_repository.get_supabase", return_value=None):
            from app.repositories.forecast_repository import fetch_forecast
            result = fetch_forecast("H001", 7)
            assert len(result["points"]) == 7

    def test_forecast_point_fields(self):
        with patch("app.repositories.forecast_repository.get_supabase", return_value=None):
            from app.repositories.forecast_repository import fetch_forecast
            point = fetch_forecast("H001", 1)["points"][0]
            for field in ("forecast_date", "predicted_admissions",
                          "confidence_lower", "confidence_upper", "risk_status"):
                assert field in point, f"Missing field '{field}'"

    def test_confidence_bounds_valid(self):
        with patch("app.repositories.forecast_repository.get_supabase", return_value=None):
            from app.repositories.forecast_repository import fetch_forecast
            for point in fetch_forecast("H001", 7)["points"]:
                assert point["confidence_lower"] <= point["predicted_admissions"]
                assert point["predicted_admissions"] <= point["confidence_upper"]

    def test_forecast_dates_are_future(self):
        with patch("app.repositories.forecast_repository.get_supabase", return_value=None):
            from app.repositories.forecast_repository import fetch_forecast
            today = str(date.today())
            for point in fetch_forecast("H001", 7)["points"]:
                assert str(point["forecast_date"]) > today


# ── mock_data internal consistency ───────────────────────────────────────────

class TestMockDataConsistency:
    def test_all_hospitals_have_valid_risk_status(self):
        from app.mock_data import HOSPITALS
        valid = {"green", "amber", "red", "critical"}
        for hid, h in HOSPITALS.items():
            assert h["risk_status"] in valid, f"{hid} has invalid risk_status"

    def test_occupancy_matches_capacity(self):
        from app.mock_data import HOSPITALS
        for hid, h in HOSPITALS.items():
            expected = round(
                (h["capacity_total"] - h["capacity_available"]) / h["capacity_total"] * 100, 1
            )
            assert abs(h["occupancy_pct"] - expected) < 1.0, (
                f"{hid} occupancy_pct mismatch: stored {h['occupancy_pct']}, computed {expected}"
            )

    def test_no_real_hospital_ids(self):
        """Ensure demo hospital IDs follow the H-code pattern and are labelled [DEMO]."""
        from app.mock_data import HOSPITALS
        for hid, h in HOSPITALS.items():
            assert hid.startswith("H"), f"hospital_id '{hid}' must start with H"
            assert "[DEMO]" in h["name"], f"Hospital '{hid}' name must contain [DEMO]"
