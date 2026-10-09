"""
test_ml_adapter.py — unit tests for the ML adapter.

Uses a lightweight fake model so no real joblib artifact is needed.
All tests reset module state before each run via ml_adapter.reset_model().
"""

import pytest
from unittest.mock import MagicMock, patch
from app.integrations.ml_adapter import (
    MLFeatures,
    MLPrediction,
    predict,
    load_model,
    is_model_loaded,
    get_model_version,
    reset_model,
    ModelUnavailableError,
    ModelPredictionError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_model():
    """Reset adapter state before every test."""
    reset_model()
    yield
    reset_model()


def _make_features(**overrides) -> MLFeatures:
    defaults = dict(
        temperature_max_c=35.0,
        temperature_min_c=22.0,
        humidity_pct=68.0,
        heat_index_c=39.0,
        occupancy_pct=76.0,
        capacity_total=300,
        day_of_week=2,
        month=10,
    )
    defaults.update(overrides)
    return MLFeatures(**defaults)


def _fake_model(return_value) -> MagicMock:
    """Build a mock that behaves like a sklearn model."""
    m = MagicMock()
    m.predict.return_value = return_value
    m.version = "v-test"
    return m


# Module-level class so joblib/pickle can locate it by qualified name
class _PicklableModel:
    """Minimal real model used in load_model tests (MagicMock can't be pickled)."""
    version = "v-test"

    def predict(self, X):
        return [[42.0, 36.0, 48.0]]


# ---------------------------------------------------------------------------
# load_model
# ---------------------------------------------------------------------------

class TestLoadModel:
    def test_warns_when_artifact_missing(self, caplog):
        with patch("app.integrations.ml_adapter.os.path.exists", return_value=False):
            load_model()
        assert not is_model_loaded()
        assert "not found" in caplog.text.lower()

    def test_loads_valid_artifact(self, tmp_path):
        import joblib
        artifact = tmp_path / "model.joblib"
        joblib.dump(_PicklableModel(), artifact)

        with patch("app.integrations.ml_adapter.get_settings") as mock_cfg:
            mock_cfg.return_value.ml_model_path = str(artifact)
            load_model()

        assert is_model_loaded()

    def test_handles_corrupt_artifact(self, tmp_path, caplog):
        corrupt = tmp_path / "bad.joblib"
        corrupt.write_bytes(b"not a real joblib file")

        with patch("app.integrations.ml_adapter.get_settings") as mock_cfg:
            mock_cfg.return_value.ml_model_path = str(corrupt)
            load_model()

        assert not is_model_loaded()
        assert "failed" in caplog.text.lower()


# ---------------------------------------------------------------------------
# predict — model not loaded
# ---------------------------------------------------------------------------

class TestPredictNoModel:
    def test_raises_model_unavailable(self):
        with pytest.raises(ModelUnavailableError):
            predict(_make_features())

    def test_error_message_is_helpful(self):
        with pytest.raises(ModelUnavailableError, match="ML model is not loaded"):
            predict(_make_features())


# ---------------------------------------------------------------------------
# predict — 3-column output (point + CI bounds)
# ---------------------------------------------------------------------------

class TestPredictThreeColumnOutput:
    def setup_method(self):
        import app.integrations.ml_adapter as adapter
        adapter._model = _fake_model([[45.0, 38.0, 52.0]])
        adapter._model_version = "v-test"

    def test_returns_ml_prediction(self):
        result = predict(_make_features())
        assert isinstance(result, MLPrediction)

    def test_predicted_admissions(self):
        result = predict(_make_features())
        assert result.predicted_admissions == 45.0

    def test_confidence_lower(self):
        result = predict(_make_features())
        assert result.confidence_lower == 38.0

    def test_confidence_upper(self):
        result = predict(_make_features())
        assert result.confidence_upper == 52.0


# ---------------------------------------------------------------------------
# predict — 1-column output (only point estimate, no CI)
# ---------------------------------------------------------------------------

class TestPredictOneColumnOutput:
    def setup_method(self):
        import app.integrations.ml_adapter as adapter
        adapter._model = _fake_model([40.0])
        adapter._model_version = "v-test"

    def test_fallback_confidence_bounds(self):
        result = predict(_make_features())
        assert result.predicted_admissions == 40.0
        assert result.confidence_lower == pytest.approx(40.0 * 0.85, abs=0.01)
        assert result.confidence_upper == pytest.approx(40.0 * 1.15, abs=0.01)


# ---------------------------------------------------------------------------
# predict — clamps negatives to zero
# ---------------------------------------------------------------------------

class TestPredictNegativeClamping:
    def setup_method(self):
        import app.integrations.ml_adapter as adapter
        adapter._model = _fake_model([[-5.0, -2.0, 1.0]])
        adapter._model_version = "v-test"

    def test_negative_prediction_clamped(self):
        result = predict(_make_features())
        assert result.predicted_admissions == 0.0
        assert result.confidence_lower == 0.0


# ---------------------------------------------------------------------------
# predict — model raises during inference
# ---------------------------------------------------------------------------

class TestPredictModelError:
    def setup_method(self):
        import app.integrations.ml_adapter as adapter
        m = MagicMock()
        m.predict.side_effect = RuntimeError("CUDA OOM")
        m.version = "v-test"
        adapter._model = m
        adapter._model_version = "v-test"

    def test_raises_model_prediction_error(self):
        with pytest.raises(ModelPredictionError):
            predict(_make_features())

    def test_error_wraps_original(self):
        with pytest.raises(ModelPredictionError, match="CUDA OOM"):
            predict(_make_features())


# ---------------------------------------------------------------------------
# MLFeatures.to_list — order must match training contract
# ---------------------------------------------------------------------------

class TestMLFeaturesOrder:
    def test_to_list_length(self):
        f = _make_features()
        assert len(f.to_list()) == 8

    def test_to_list_order(self):
        f = MLFeatures(
            temperature_max_c=1.0, temperature_min_c=2.0, humidity_pct=3.0,
            heat_index_c=4.0, occupancy_pct=5.0, capacity_total=6,
            day_of_week=7, month=8,
        )
        assert f.to_list() == [1.0, 2.0, 3.0, 4.0, 5.0, 6, 7, 8]
