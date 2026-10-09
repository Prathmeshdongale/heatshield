"""Tests for model training."""

import numpy as np
import pandas as pd
import pytest
from src.core.train import ModelTrainer


@pytest.fixture
def training_df():
    n = 100
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "timestamp":    pd.date_range("2024-06-01", periods=n, freq="D"),
        "temperature":  rng.uniform(15, 38, n),
        "humidity":     rng.uniform(40, 90, n),
        "ae_attendances": rng.integers(60, 250, n).astype(float),
    })


def test_prepare_training_data(tmp_path, training_df):
    trainer = ModelTrainer(models_dir=str(tmp_path))
    X, y = trainer.prepare_training_data(training_df)
    assert len(X) > 0
    assert len(X) == len(y)


def test_train_random_forest(tmp_path, training_df):
    trainer = ModelTrainer(models_dir=str(tmp_path))
    X, y = trainer.prepare_training_data(training_df)
    model, metrics = trainer.train_model(X, y, model_name="random_forest")
    assert model is not None
    assert "r2" in metrics
    assert "mae" in metrics


def test_train_gradient_boosting(tmp_path, training_df):
    trainer = ModelTrainer(models_dir=str(tmp_path))
    X, y = trainer.prepare_training_data(training_df)
    model, metrics = trainer.train_model(X, y, model_name="gradient_boosting")
    assert "r2" in metrics


def test_train_ridge(tmp_path, training_df):
    trainer = ModelTrainer(models_dir=str(tmp_path))
    X, y = trainer.prepare_training_data(training_df)
    model, metrics = trainer.train_model(X, y, model_name="ridge")
    assert "r2" in metrics


def test_select_best_model(tmp_path, training_df):
    trainer = ModelTrainer(models_dir=str(tmp_path))
    X, y = trainer.prepare_training_data(training_df)
    results = trainer.train_all_models(X, y)
    best_name, best_model, best_metrics = trainer.select_best_model(results)
    assert best_name in results
    assert best_model is not None


def test_save_and_load(tmp_path, training_df):
    trainer = ModelTrainer(models_dir=str(tmp_path))
    X, y = trainer.prepare_training_data(training_df)
    model, _ = trainer.train_model(X, y)
    saved = trainer.save_model(model, "test_model", "v1")
    assert saved.exists()
    loaded = trainer.load_model("test_model", "v1")
    assert loaded is not None
