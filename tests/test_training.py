"""Tests for model training module."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from app.ml.train import ModelTrainer
from app.ml.features import FeatureEngineer
from app.ml.preprocessing import DataPreprocessor


@pytest.fixture
def sample_training_data():
    """Create sample training data."""
    n_samples = 100
    return pd.DataFrame({
        "timestamp": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temperature": np.random.uniform(20, 35, n_samples),
        "humidity": np.random.uniform(40, 80, n_samples),
        "a&e_visits": np.random.randint(80, 200, n_samples),
    })


@pytest.fixture
def trainer(tmp_path):
    """Create ModelTrainer instance."""
    return ModelTrainer(models_dir=str(tmp_path))


@pytest.fixture
def feature_engineer():
    """Create FeatureEngineer instance."""
    return FeatureEngineer()


@pytest.fixture
def preprocessor():
    """Create DataPreprocessor instance."""
    return DataPreprocessor()


def test_prepare_training_data(trainer, sample_training_data):
    """Test training data preparation."""
    X, y = trainer.prepare_training_data(sample_training_data)
    assert len(X) > 0
    assert len(y) > 0
    assert len(X) == len(y)


def test_train_random_forest_model(trainer, sample_training_data):
    """Test training random forest model."""
    X, y = trainer.prepare_training_data(sample_training_data)
    model, metrics = trainer.train_model(X, y, model_name="random_forest")

    assert model is not None
    assert "r2" in metrics
    assert "mae" in metrics
    assert metrics["r2"] >= -1  # R² can be negative for bad models


def test_train_gradient_boosting_model(trainer, sample_training_data):
    """Test training gradient boosting model."""
    X, y = trainer.prepare_training_data(sample_training_data)
    model, metrics = trainer.train_model(X, y, model_name="gradient_boosting")

    assert model is not None
    assert "r2" in metrics


def test_train_ridge_model(trainer, sample_training_data):
    """Test training ridge regression model."""
    X, y = trainer.prepare_training_data(sample_training_data)
    model, metrics = trainer.train_model(X, y, model_name="ridge")

    assert model is not None
    assert "r2" in metrics


def test_select_best_model(trainer, sample_training_data):
    """Test model selection."""
    X, y = trainer.prepare_training_data(sample_training_data)
    results = trainer.train_all_models(X, y)

    best_name, best_model, best_metrics = trainer.select_best_model(results)

    assert best_name in results
    assert best_model is not None


def test_save_and_load_model(trainer, sample_training_data, tmp_path):
    """Test model save and load."""
    X, y = trainer.prepare_training_data(sample_training_data)
    model, _ = trainer.train_model(X, y)

    saved_path = trainer.save_model(model, "test_model", "v1")
    assert saved_path.exists()

    loaded_model = trainer.load_model("test_model", "v1")
    assert loaded_model is not None


def test_get_model_metrics(trainer, sample_training_data, tmp_path):
    """Test getting model metrics."""
    X, y = trainer.prepare_training_data(sample_training_data)
    model, metrics = trainer.train_model(X, y)

    trainer.save_model(model, "test_model", "v1")

    saved_metrics = trainer.get_model_metrics("test_model", "v1")
    assert "r2" in saved_metrics
