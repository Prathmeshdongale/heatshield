"""Tests for the Predictor class."""

import numpy as np
import pytest
from src.core.predict import Predictor


def test_predict_single(tiny_model):
    p = Predictor(tiny_model)
    result = p.predict_single(np.array([0.5, 0.5]))
    assert isinstance(result, float)
    assert result >= 0


def test_predict_batch(tiny_model):
    p = Predictor(tiny_model)
    X = np.array([[0.3, 0.7], [0.8, 0.2], [0.5, 0.5]])
    preds = p.predict_batch(X)
    assert len(preds) == 3
    assert all(v >= 0 for v in preds)


def test_predict_with_confidence(tiny_model):
    p = Predictor(tiny_model)
    X = np.array([[0.5, 0.5], [0.3, 0.7]])
    result = p.predict_with_confidence(X)
    assert "predictions" in result
    assert "lower" in result
    assert "upper" in result
    assert all(result["lower"] <= result["predictions"])
    assert all(result["predictions"] <= result["upper"])


def test_no_model_raises(sample_df):
    p = Predictor()
    with pytest.raises(ValueError, match="No model set"):
        p.predict_single(np.array([0.5, 0.5]))


def test_set_model(tiny_model):
    p = Predictor()
    p.set_model(tiny_model)
    assert p.model is not None


def test_non_negative_predictions(tiny_model):
    p = Predictor(tiny_model)
    X = np.random.default_rng(0).uniform(0, 1, (20, 2))
    assert all(p.predict_batch(X) >= 0)
