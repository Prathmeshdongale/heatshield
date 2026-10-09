"""
test_ml_adapter.py — unit tests for the ML adapter.
Uses lightweight fake models — no real joblib artifact needed.
All tests reset module state via reset_model().
"""

import pytest
from unittest.mock import MagicMock, patch
from app.integrations.ml_adapter import (
    MLFeatures,
    MLPrediction,
    FEATURE_ORDER,
    predict,
    load_model,
    is_model_loaded,
    get_model_version,
    reset_model,
    ModelUnavailableError,
    ModelPredictionError,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_model():
    reset_model()
    yield
    reset_model()


def _make_features() -> MLFeatures:
    """Default MLFeatures with all fields set."""
    return MLFeatures()


def _fake_model(return_value) -> MagicMock:
    m = MagicMock()
    m.predict.return_value = return_value
    m.version = "v1.0.0"
    return m


class _PicklableModel:
    """Minimal real model (MagicMock can't be pickled)."""
    version = "v1.0.0"
    def predict(self, X):
        return [99.0]


# ── load_model ────────────────────────────────────────────────────────────────

class TestLoadModel:
    def test_warns_when_artifact_missing(self, caplog):
        with patch("app.integrations.ml_adapter.os.path.exists", return_value=False):
            load_model()
        assert not is_model_loaded()

    def test_loads_valid_artifact(self, tmp_path):
        import joblib
        artifact = tmp_path / "model.joblib"
        joblib.dump(_PicklableModel(), artifact)
        with patch("app.integrations.ml_adapter.get_settings") as mock_cfg:
            mock_cfg.return_value.ml_model_path_abs = str(artifact)
            load_model()
        assert is_model_loaded()

    def test_handles_corrupt_artifact(self, tmp_path, caplog):
        bad = tmp_path / "bad.joblib"
        bad.write_bytes(b"not a joblib file")
        with patch("app.integrations.ml_adapter.get_settings") as mock_cfg:
            mock_cfg.return_value.ml_model_path_abs = str(bad)
            load_model()
        assert not is_model_loaded()


# ── predict — no model ────────────────────────────────────────────────────────

class TestPredictNoModel:
    def test_raises_model_unavailable(self):
        with pytest.raises(ModelUnavailableError):
            predict(_make_features())

    def test_error_message(self):
        with pytest.raises(ModelUnavailableError, match="not loaded"):
            predict(_make_features())


# ── predict — scalar output ───────────────────────────────────────────────────

class TestPredictScalarOutput:
    def setup_method(self):
        import app.integrations.ml_adapter as a
        a._model = _fake_model([80.0])
        a._model_version = "v1.0.0"

    def test_returns_ml_prediction(self):
        assert isinstance(predict(_make_features()), MLPrediction)

    def test_predicted_admissions(self):
        assert predict(_make_features()).predicted_admissions == 80.0

    def test_confidence_interval_applied(self):
        r = predict(_make_features())
        assert r.confidence_lower == pytest.approx(80.0 * 0.85, abs=0.01)
        assert r.confidence_upper == pytest.approx(80.0 * 1.15, abs=0.01)

    def test_non_negative_output(self):
        import app.integrations.ml_adapter as a
        a._model = _fake_model([-5.0])
        r = predict(_make_features())
        assert r.predicted_admissions == 0.0
        assert r.confidence_lower == 0.0


# ── predict — model raises ────────────────────────────────────────────────────

class TestPredictModelError:
    def setup_method(self):
        import app.integrations.ml_adapter as a
        m = MagicMock()
        m.predict.side_effect = RuntimeError("inference failed")
        m.version = "v1.0.0"
        a._model = m
        a._model_version = "v1.0.0"

    def test_raises_model_prediction_error(self):
        with pytest.raises(ModelPredictionError):
            predict(_make_features())

    def test_error_wraps_original(self):
        with pytest.raises(ModelPredictionError, match="inference failed"):
            predict(_make_features())


# ── MLFeatures.to_list ────────────────────────────────────────────────────────

class TestMLFeaturesOrder:
    def test_to_list_length(self):
        assert len(_make_features().to_list()) == len(FEATURE_ORDER)

    def test_to_list_matches_feature_order(self):
        f = _make_features()
        lst = f.to_list()
        for i, col in enumerate(FEATURE_ORDER):
            assert lst[i] == getattr(f, col), f"Mismatch at index {i}: {col}"

    def test_feature_order_length(self):
        assert len(FEATURE_ORDER) == 31
