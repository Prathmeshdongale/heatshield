"""
test_forecast_service.py — unit tests for forecast_service.

Key behaviours verified:
  - Demo mode returns demo data and never calls the ML adapter.
  - Live mode calls the adapter and builds the response from its output.
  - Live mode raises ForecastUnavailableError on model failure — never
    silently substitutes data.
  - Unknown hospital raises HospitalNotFoundError.
  - Risk status comes from calculate_risk(), not from the model output.
"""

import pytest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock
from app.services.forecast_service import (
    get_forecast,
    ForecastUnavailableError,
)
from app.services.capacity_service import HospitalNotFoundError
from app.integrations.ml_adapter import (
    MLPrediction,
    ModelUnavailableError,
    ModelPredictionError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _settings(demo=True):
    s = MagicMock()
    s.demo_mode = demo
    s.supabase_url = "" if demo else "https://fake.supabase.co"
    return s


def _fake_prediction(admissions=40.0, lower=34.0, upper=46.0):
    return MLPrediction(
        predicted_admissions=admissions,
        confidence_lower=lower,
        confidence_upper=upper,
    )


_HOSPITAL = {
    "hospital_id": "H001",
    "name": "Test Hospital",
    "region": "Test",
    "address": "1 Test St",
    "latitude": 51.5,
    "longitude": -0.1,
    "contact_email": "t@t.nhs",
    "capacity_total": 300,
    "capacity_available": 72,
    "occupancy_pct": 76.0,
    "risk_status": "amber",
}

_WEATHER = {
    "hospital_id": "H001",
    "days_requested": 1,
    "observations": [{
        "observation_date": "2026-10-09",
        "temperature_max_c": 35.0,
        "temperature_min_c": 22.0,
        "humidity_pct": 68.0,
        "heat_index_c": 39.0,
        "condition": "Heatwave",
    }],
}

# Shared live-mode patches applied via ExitStack
_LIVE_PATCHES = [
    ("app.services.forecast_service.fetch_hospital_by_id", _HOSPITAL),
    ("app.services.forecast_service.is_model_loaded",      True),
    ("app.services.forecast_service.fetch_weather",        _WEATHER),
    ("app.services.forecast_service.save_forecast_points", True),
]


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

class TestGetForecastDemoMode:
    def test_returns_demo_source(self):
        with patch("app.services.forecast_service.get_settings", return_value=_settings(demo=True)):
            _, source = get_forecast("H001", 7)
        assert source == "demo"

    def test_returns_correct_day_count(self):
        with patch("app.services.forecast_service.get_settings", return_value=_settings(demo=True)):
            forecast, _ = get_forecast("H001", 5)
        assert len(forecast["points"]) == 5

    def test_unknown_hospital_raises(self):
        with patch("app.services.forecast_service.get_settings", return_value=_settings(demo=True)):
            with pytest.raises(HospitalNotFoundError):
                get_forecast("ZZZZ", 7)

    def test_ml_adapter_never_called_in_demo(self):
        with patch("app.services.forecast_service.get_settings", return_value=_settings(demo=True)), \
             patch("app.services.forecast_service.ml_predict") as mock_predict:
            get_forecast("H001", 3)
        mock_predict.assert_not_called()

    def test_invalid_days_raises_value_error(self):
        with patch("app.services.forecast_service.get_settings", return_value=_settings(demo=True)):
            with pytest.raises(ValueError):
                get_forecast("H001", 0)


# ---------------------------------------------------------------------------
# Live mode — happy path
# ---------------------------------------------------------------------------

class TestGetForecastLiveMode:
    def test_returns_live_source(self):
        with ExitStack() as stack:
            stack.enter_context(patch("app.services.forecast_service.get_settings",
                                      return_value=_settings(demo=False)))
            for target, val in _LIVE_PATCHES:
                stack.enter_context(patch(target, return_value=val))
            stack.enter_context(patch("app.services.forecast_service.ml_predict",
                                      return_value=_fake_prediction()))
            stack.enter_context(patch("app.services.forecast_service.get_model_version",
                                      return_value="v-test"))
            _, source = get_forecast("H001", 7)
        assert source == "live"

    def test_returns_correct_day_count(self):
        with ExitStack() as stack:
            stack.enter_context(patch("app.services.forecast_service.get_settings",
                                      return_value=_settings(demo=False)))
            for target, val in _LIVE_PATCHES:
                stack.enter_context(patch(target, return_value=val))
            stack.enter_context(patch("app.services.forecast_service.ml_predict",
                                      return_value=_fake_prediction()))
            stack.enter_context(patch("app.services.forecast_service.get_model_version",
                                      return_value="v-test"))
            forecast, _ = get_forecast("H001", 3)
        assert len(forecast["points"]) == 3

    def test_point_fields_present(self):
        with ExitStack() as stack:
            stack.enter_context(patch("app.services.forecast_service.get_settings",
                                      return_value=_settings(demo=False)))
            for target, val in _LIVE_PATCHES:
                stack.enter_context(patch(target, return_value=val))
            stack.enter_context(patch("app.services.forecast_service.ml_predict",
                                      return_value=_fake_prediction()))
            stack.enter_context(patch("app.services.forecast_service.get_model_version",
                                      return_value="v-test"))
            forecast, _ = get_forecast("H001", 1)
        p = forecast["points"][0]
        for field in ("forecast_date", "predicted_admissions",
                      "confidence_lower", "confidence_upper", "risk_status"):
            assert field in p, f"Missing field: {field}"

    def test_risk_computed_not_blindly_copied(self):
        """risk_status must come from calculate_risk(), not from the model output."""
        with ExitStack() as stack:
            stack.enter_context(patch("app.services.forecast_service.get_settings",
                                      return_value=_settings(demo=False)))
            for target, val in _LIVE_PATCHES:
                stack.enter_context(patch(target, return_value=val))
            stack.enter_context(patch("app.services.forecast_service.ml_predict",
                                      return_value=_fake_prediction(admissions=40.0)))
            stack.enter_context(patch("app.services.forecast_service.get_model_version",
                                      return_value="v-test"))
            forecast, _ = get_forecast("H001", 1)
        # 40 admissions / 300 capacity = 13.3 % → green
        assert forecast["points"][0]["risk_status"] == "green"

    def test_model_version_in_response(self):
        with ExitStack() as stack:
            stack.enter_context(patch("app.services.forecast_service.get_settings",
                                      return_value=_settings(demo=False)))
            for target, val in _LIVE_PATCHES:
                stack.enter_context(patch(target, return_value=val))
            stack.enter_context(patch("app.services.forecast_service.ml_predict",
                                      return_value=_fake_prediction()))
            stack.enter_context(patch("app.services.forecast_service.get_model_version",
                                      return_value="v-test"))
            forecast, _ = get_forecast("H001", 1)
        assert forecast["model_version"] == "v-test"

    def test_unknown_hospital_raises_404(self):
        with patch("app.services.forecast_service.get_settings",
                   return_value=_settings(demo=False)), \
             patch("app.services.forecast_service.fetch_hospital_by_id", return_value=None):
            with pytest.raises(HospitalNotFoundError):
                get_forecast("ZZZZ", 7)


# ---------------------------------------------------------------------------
# Live mode — model failures must raise 503, never substitute data
# ---------------------------------------------------------------------------

class TestGetForecastLiveModeModelFailure:

    def _run_with_predict_error(self, exc):
        with ExitStack() as stack:
            stack.enter_context(patch("app.services.forecast_service.get_settings",
                                      return_value=_settings(demo=False)))
            for target, val in _LIVE_PATCHES:
                stack.enter_context(patch(target, return_value=val))
            stack.enter_context(patch("app.services.forecast_service.ml_predict",
                                      side_effect=exc))
            stack.enter_context(patch("app.services.forecast_service.get_model_version",
                                      return_value="v-test"))
            get_forecast("H001", 7)

    def test_model_unavailable_raises_forecast_unavailable(self):
        with pytest.raises(ForecastUnavailableError):
            self._run_with_predict_error(ModelUnavailableError("no model"))

    def test_model_prediction_error_raises_forecast_unavailable(self):
        with pytest.raises(ForecastUnavailableError):
            self._run_with_predict_error(ModelPredictionError("inference failed"))

    def test_model_not_loaded_raises_immediately(self):
        with patch("app.services.forecast_service.get_settings",
                   return_value=_settings(demo=False)), \
             patch("app.services.forecast_service.fetch_hospital_by_id",
                   return_value=_HOSPITAL), \
             patch("app.services.forecast_service.is_model_loaded",
                   return_value=False):
            with pytest.raises(ForecastUnavailableError):
                get_forecast("H001", 7)

    def test_no_demo_data_substituted_on_model_failure(self):
        """Confirm exception type — demo data must never silently replace a failed prediction."""
        with pytest.raises(ForecastUnavailableError):
            self._run_with_predict_error(ModelUnavailableError("down"))
