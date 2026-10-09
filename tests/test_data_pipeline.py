"""Tests for data pipeline module."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from app.ml.pipeline import HeatShieldPipeline
from app.config import settings


@pytest.fixture
def sample_data():
    """Create sample data for pipeline testing."""
    n_samples = 30
    return pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temp_mean": [25.0 + i * 0.5 for i in range(n_samples)],
        "temp_max": [30.0 + i * 0.5 for i in range(n_samples)],
        "temp_min": [20.0 + i * 0.5 for i in range(n_samples)],
        "humidity": [50.0 + i for i in range(n_samples)],
        "ed_visits_heat": [100 + i for i in range(n_samples)],
    })


@pytest.fixture
def sample_data_inference():
    """Create inference data (no target)."""
    n_samples = 10
    return pd.DataFrame({
        "date": pd.date_range("2023-07-01", periods=n_samples, freq="D"),
        "temp_mean": [28.0 + i * 0.5 for i in range(n_samples)],
        "humidity": [55.0 + i for i in range(n_samples)],
    })


class TestPipelineInitialization:
    """Tests for pipeline initialization."""

    def test_pipeline_creates_directories(self, tmp_path):
        """Test that pipeline creates required directories."""
        pipeline = HeatShieldPipeline(
            data_dir=str(tmp_path / "data"),
            reports_dir=str(tmp_path / "reports"),
        )

        assert pipeline.data_dir.exists()
        assert pipeline.reports_dir.exists()

    def test_pipeline_components_initialized(self, sample_data):
        """Test that pipeline components are properly initialized."""
        pipeline = HeatShieldPipeline()

        assert pipeline.feature_engineer is not None
        assert pipeline.preprocessor is not None
        assert pipeline.validator is not None


class TestPipelineFit:
    """Tests for pipeline fitting."""

    def test_pipeline_fit(self, sample_data):
        """Test pipeline fitting on training data."""
        pipeline = HeatShieldPipeline()

        df_processed, stats = pipeline.prepare_training_data(sample_data)

        assert pipeline.fitted
        assert len(df_processed.columns) > len(sample_data.columns)
        assert "feature_columns" in stats
        assert "preprocess_stats" in stats

    def test_pipeline_fit_saves_stats(self, sample_data, tmp_path):
        """Test that pipeline saves transformation statistics."""
        pipeline = HeatShieldPipeline(reports_dir=str(tmp_path))

        df_processed, stats = pipeline.prepare_training_data(sample_data, save_stats=True)

        # Check that stats file was created
        stats_file = tmp_path / "transformation_stats.json"
        assert stats_file.exists()

    def test_pipeline_fit_requires_target(self, sample_data):
        """Test that pipeline requires target column."""
        # Remove target column
        df = sample_data.drop(columns=[settings.target_column])

        pipeline = HeatShieldPipeline()

        with pytest.raises(ValueError, match="not found"):
            pipeline.prepare_training_data(df)


class TestPipelineInference:
    """Tests for pipeline inference mode."""

    def test_pipeline_inference(self, sample_data, sample_data_inference):
        """Test pipeline inference on new data."""
        pipeline = HeatShieldPipeline()

        # First fit on training data
        pipeline.prepare_training_data(sample_data)

        # Then prepare inference data
        df_inference, validation = pipeline.prepare_inference_data(sample_data_inference)

        assert validation["valid"]
        assert len(df_inference.columns) > 0

    def test_pipeline_inference_requires_fit(self, sample_data_inference):
        """Test that inference requires prior fitting."""
        pipeline = HeatShieldPipeline()

        with pytest.raises(RuntimeError, match="fitted"):
            pipeline.prepare_inference_data(sample_data_inference)

    def test_pipeline_inference_validates_features(self, sample_data, sample_data_inference):
        """Test that inference validates required features."""
        pipeline = HeatShieldPipeline()

        # Fit on full data
        pipeline.prepare_training_data(sample_data)

        # Remove a required feature
        df_incomplete = sample_data_inference.drop(columns=["temp_mean"])

        with pytest.raises(ValueError, match="Missing features"):
            pipeline.prepare_inference_data(df_incomplete)


class TestPipelineDataValidation:
    """Tests for pipeline data validation."""

    def test_validate_training_data(self, sample_data):
        """Test training data validation."""
        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(sample_data)

        assert is_valid
        assert "errors" in summary
        assert "warnings" in summary

    def test_validate_training_data_missing_target(self, sample_data):
        """Test validation with missing target."""
        df = sample_data.drop(columns=[settings.target_column])

        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(df)

        assert not is_valid
        assert len(summary["errors"]) > 0

    def test_validate_training_data_with_leakage(self, sample_data):
        """Test validation with potential leakage."""
        # Shuffle data to simulate leakage
        df = sample_data.sample(frac=1)

        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(df)

        # Should detect the ordering issue
        assert not is_valid


class TestPipelineFeatureColumns:
    """Tests for pipeline feature column management."""

    def test_get_feature_columns(self, sample_data):
        """Test getting feature columns."""
        pipeline = HeatShieldPipeline()

        pipeline.prepare_training_data(sample_data)
        feature_cols = pipeline.get_feature_columns()

        assert len(feature_cols) > 0
        assert isinstance(feature_cols, list)
        assert settings.target_column not in feature_cols

    def test_feature_columns_include_expected(self, sample_data):
        """Test that feature columns include expected types."""
        pipeline = HeatShieldPipeline()

        pipeline.prepare_training_data(sample_data)
        feature_cols = pipeline.get_feature_columns()

        # Check for various feature types
        has_calendar = any(c in feature_cols for c in ["month", "season"])
        has_lag = any("lag" in c for c in feature_cols)
        has_rolling = any("rolling" in c for c in feature_cols)
        has_weather = any("temp" in c or "humidity" in c for c in feature_cols)

        assert has_calendar
        assert has_lag
        assert has_rolling
        assert has_weather


class TestPipelineDatasetSchema:
    """Tests for pipeline dataset schema generation."""

    def test_generate_dataset_schema(self, sample_data):
        """Test dataset schema generation."""
        pipeline = HeatShieldPipeline()

        pipeline.prepare_training_data(sample_data)
        schema = pipeline.generate_dataset_schema()

        assert "schema_version" in schema
        assert "target" in schema
        assert "input_columns" in schema
        assert schema["target"]["name"] == settings.target_column

    def test_generate_schema_after_fit(self, sample_data):
        """Test schema generation after fitting."""
        pipeline = HeatShieldPipeline()

        # Before fit, schema might be incomplete
        schema_before = pipeline.generate_dataset_schema()
        assert "input_columns" in schema_before

        # After fit, should have full feature list
        pipeline.prepare_training_data(sample_data)
        schema_after = pipeline.generate_dataset_schema()

        assert len(schema_after["input_columns"]) > 0


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    def test_full_training_pipeline(self, sample_data, tmp_path):
        """Test the full training pipeline."""
        pipeline = HeatShieldPipeline(
            data_dir=str(tmp_path / "data"),
            reports_dir=str(tmp_path / "reports"),
        )

        # Prepare data
        df_processed, stats = pipeline.prepare_training_data(sample_data)

        # Verify output
        assert len(df_processed) > 0
        assert pipeline.fitted

        # Verify stats
        assert "created_at" in stats
        assert "feature_columns" in stats

        # Generate schema
        schema = pipeline.generate_dataset_schema()
        assert "feature_statistics" in schema

    def test_train_and_inference_pipeline(self, sample_data, sample_data_inference, tmp_path):
        """Test training and inference in same pipeline."""
        pipeline = HeatShieldPipeline(
            data_dir=str(tmp_path / "data"),
            reports_dir=str(tmp_path / "reports"),
        )

        # Train
        pipeline.prepare_training_data(sample_data)

        # Inference
        df_inference, _ = pipeline.prepare_inference_data(sample_data_inference)

        # Both should have the same feature columns
        train_features = pipeline.get_feature_columns()
        inference_features = [c for c in df_inference.columns if c != settings.target_column]

        # Check that key features match
        assert "month" in train_features
        assert "month" in inference_features


class TestPipelineErrorHandling:
    """Tests for pipeline error handling."""

    def test_load_data_not_found(self):
        """Test error handling for missing data file."""
        pipeline = HeatShieldPipeline()

        with pytest.raises(FileNotFoundError):
            pipeline.load_data("nonexistent_file.csv")

    def test_prepare_inference_not_fitted(self, sample_data_inference):
        """Test error handling for inference without fitting."""
        pipeline = HeatShieldPipeline()

        with pytest.raises(RuntimeError, match="fitted"):
            pipeline.prepare_inference_data(sample_data_inference)

    def test_save_stats_empty(self, sample_data, tmp_path):
        """Test saving stats when pipeline not fitted."""
        pipeline = HeatShieldPipeline(reports_dir=str(tmp_path))

        # Should not crash even if not fitted
        pipeline.save_transformation_stats()
        stats_file = tmp_path / "transformation_stats.json"
        assert stats_file.exists()
