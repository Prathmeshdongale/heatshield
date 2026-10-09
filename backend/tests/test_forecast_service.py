"""
test_forecast_service.py — unit tests for forecast_service.
No demo mode — all data comes from DB or ML. Repository calls mocked.
"""

import pytest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock
from app.services.forecast_service import get_forecast, ForecastUnavailableError
from app.services.capacity_service import HospitalNotFoundError
from app.integrations.ml_adapter import MLPrediction, ModelUnavailableError, ModelPredictionError


def _fake_prediction(admissions=40.0, lower=34.0, upper=46.0):
    return MLPrediction(predicted_admissions=admissions, confidence_lower=lower, confidence_upper=upper)


_HOSPITAL = {
    "hospital_id": "H001", "name": "Test Hospital", "region": "Test",
    "address": "1 Test St", "latitude": 51.5, "longitude": -0.1,
    "contact_email": "t@t.nhs", "capacity_total": 300,
    "capacity_available": 72, "occupancy_pct": 76.0, "risk_status": "amber",
}

_WEATHER = {
    "hospital_id": "H001", "days_requested": 1,
    "observations": [{"observation_date": "2026-10-09", "temperature_max_c": 35.0,
                      "temperature_min_c": 22.0, "humidity_pct": 68.0,
                      "heat_index_c": 39.0, "condition": "Heatwave"}],
}

_STORED_FORECAST = {
    "hospital_id": "H001", "model_version": "v1.2.0-demo",
    "generated_at": "2026-10-09T00:00:00+00:00", "days_requested": 7,
    "points": [{"forecast_date": "2026-10-10", "predicted_admissions": 42.5,
                "confidence_lower": 36.1, "confidence_upper": 48.9, "risk_status": "amber"}],
}

_LIVE_PATCHES = [
    ("app.services.forecast_service.fetch_hospital_by_id", _HOSPITAL),
    ("app.services.forecast_service.is_model_loaded",      True),
    ("app.services.forecast_service.fetch_weather",        _WEATHER),
    ("app.services.forecast_service.save_forecast_points", True),
]


# ── Happy path (model loaded) ──────────────────────────────────────────────────

class TestGetForecastWithModel:
    def test_returns_live_source(self):
        with ExitStack() as s:
            for t, v in _LIVE_PATCHES: s.enter_context(patch(t, return_value=v))
            s.enter_context(patch("app.services.forecast_service.ml_predict",
                                  return_value=_fake_prediction()))
            s.enter_context(patch("app.services.forecast_service.get_model_version",
                                  return_value="v-test"))
            _, source = get_forecast("H001", 7)
        assert source == "live"

    def test_correct_day_count(self):
        with ExitStack() as s:
            for t, v in _LIVE_PATCHES: s.enter_context(patch(t, return_value=v))
            s.enter_context(patch("app.services.forecast_service.ml_predict",
                                  return_value=_fake_prediction()))
            s.enter_context(patch("app.services.forecast_service.get_model_version",
                                  return_value="v-test"))
            forecast, _ = get_forecast("H001", 3)
        assert len(forecast["points"]) == 3

    def test_point_fields_present(self):
        with ExitStack() as s:
            for t, v in _LIVE_PATCHES: s.enter_context(patch(t, return_value=v))
            s.enter_context(patch("app.services.forecast_service.ml_predict",
                                  return_value=_fake_prediction()))
            s.enter_context(patch("app.services.forecast_service.get_model_version",
                                  return_value="v-test"))
            forecast, _ = get_forecast("H001", 1)
        p = forecast["points"][0]
        for field in ("forecast_date", "predicted_admissions",
                      "confidence_lower", "confidence_upper", "risk_status"):
            assert field in p, f"Missing field: {field}"

    def test_risk_computed_from_capacity(self):
        """risk_status must come from calculate_risk(), not from the model."""
        with ExitStack() as s:
            for t, v in _LIVE_PATCHES: s.enter_context(patch(t, return_value=v))
            s.enter_context(patch("app.services.forecast_service.ml_predict",
                                  return_value=_fake_prediction(admissions=40.0)))
            s.enter_context(patch("app.services.forecast_service.get_model_version",
                                  return_value="v-test"))
            forecast, _ = get_forecast("H001", 1)
        # 40/300 = 13.3% → green
        assert forecast["points"][0]["risk_status"] == "green"

    def test_unknown_hospital_raises(self):
        with patch("app.services.forecast_service.fetch_hospital_by_id", return_value=None):
            with pytest.raises(HospitalNotFoundError):
                get_forecast("ZZZZ", 7)

    def test_invalid_days_raises_value_error(self):
        with pytest.raises(ValueError):
            get_forecast("H001", 0)


# ── No model loaded → fall back to stored DB rows ─────────────────────────────

class TestGetForecastNoModel:
    def test_returns_stored_db_forecast(self):
        with patch("app.services.forecast_service.fetch_hospital_by_id", return_value=_HOSPITAL), \
             patch("app.services.forecast_service.is_model_loaded", return_value=False), \
             patch("app.services.forecast_service.is_db_available", return_value=True), \
             patch("app.services.forecast_service.fetch_forecast",
                   return_value=_STORED_FORECAST) as mock_fetch:
            result, source = get_forecast("H001", 7)
        assert result["hospital_id"] == "H001"
        assert source == "live"
        mock_fetch.assert_called_once_with("H001", 7)

    def test_unknown_hospital_still_raises(self):
        with patch("app.services.forecast_service.fetch_hospital_by_id", return_value=None), \
             patch("app.services.forecast_service.is_model_loaded", return_value=False):
            with pytest.raises(HospitalNotFoundError):
                get_forecast("ZZZZ", 7)


# ── Model failures → ForecastUnavailableError ─────────────────────────────────

class TestGetForecastModelFailure:
    def _run_with_error(self, exc):
        with ExitStack() as s:
            for t, v in _LIVE_PATCHES: s.enter_context(patch(t, return_value=v))
            s.enter_context(patch("app.services.forecast_service.ml_predict", side_effect=exc))
            s.enter_context(patch("app.services.forecast_service.get_model_version",
                                  return_value="v-test"))
            get_forecast("H001", 7)

    def test_model_unavailable_raises(self):
        with pytest.raises(ForecastUnavailableError):
            self._run_with_error(ModelUnavailableError("no model"))

    def test_prediction_error_raises(self):
        with pytest.raises(ForecastUnavailableError):
            self._run_with_error(ModelPredictionError("inference failed"))
