"""Tests for prediction module."""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from app.ml.predict import Predictor


@pytest.fixture
def sample_features():
    """Create sample features for prediction."""
    return np.array([
        [25.0, 60.0],
        [30.0, 50.0],
        [35.0, 40.0],
    ])


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for prediction."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2023-06-01", periods=3),
        "temperature": [25.0, 30.0, 35.0],
        "humidity": [60.0, 50.0, 40.0],
    })


@pytest.fixture
def model():
    """Create trained model for prediction."""
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    X = np.array([[20.0, 60.0], [25.0, 50.0], [30.0, 40.0]])
    y = np.array([100, 120, 150])
    model.fit(X, y)
    return model


@pytest.fixture
def predictor(model):
    """Create Predictor instance."""
    return Predictor(model)


def test_predict_single(predictor, sample_features):
    """Test single prediction."""
    prediction = predictor.predict_single(sample_features[0])
    assert isinstance(prediction, float)
    assert prediction >= 0


def test_predict_batch(predictor, sample_features):
    """Test batch prediction."""
    predictions = predictor.predict_batch(sample_features)
    assert isinstance(predictions, np.ndarray)
    assert len(predictions) == len(sample_features)
    assert all(p >= 0 for p in predictions)


def test_predict_with_confidence(predictor, sample_features):
    """Test prediction with confidence intervals."""
    result = predictor.predict_with_confidence(sample_features)
    assert "predictions" in result
    assert "lower" in result
    assert "upper" in result
    assert len(result["predictions"]) == len(sample_features)


def test_generate_forecast_series(predictor, sample_dataframe):
    """Test forecast series generation."""
    result = predictor.generate_forecast_series(sample_dataframe)
    assert "predicted_demand" in result.columns
    assert "confidence_lower" in result.columns
    assert "confidence_upper" in result.columns
    assert len(result) == len(sample_dataframe)


def test_no_model_prediction():
    """Test prediction without model raises error."""
    predictor = Predictor()
    with pytest.raises(ValueError, match="No model set"):
        predictor.predict_single(np.array([25.0, 60.0]))


def test_non_negative_predictions(predictor, sample_features):
    """Test that predictions are non-negative."""
    # Create a model that might predict negative values
    X = np.array([[20.0, 60.0], [25.0, 50.0]])
    y = np.array([100, 120])
    test_model = RandomForestRegressor(n_estimators=10, random_state=42)
    test_model.fit(X, y)

    predictor.set_model(test_model)
    prediction = predictor.predict_single(sample_features[0])
    assert prediction >= 0
