"""Tests for training data preparation and validation."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from app.ml.pipeline import HeatShieldPipeline
from app.config import settings


@pytest.fixture
def minimal_training_data():
    """Create minimal training data (95 samples as per requirements)."""
    n_samples = 95
    return pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temp_mean": [25.0 + i * 0.1 for i in range(n_samples)],
        "humidity": [50.0 + i * 0.2 for i in range(n_samples)],
        "ed_visits_heat": [100 + i for i in range(n_samples)],
    })


@pytest.fixture
def data_with_weather_gaps():
    """Create data with gaps in weather features."""
    n_samples = 30
    df = pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temp_mean": [25.0 + i * 0.5 for i in range(n_samples)],
        "humidity": [50.0 + i for i in range(n_samples)],
        "ed_visits_heat": [100 + i for i in range(n_samples)],
    })
    # Add some missing values
    df.loc[5:7, "temp_mean"] = None
    return df


@pytest.fixture
def data_with_missing_target():
    """Create data with missing target values."""
    n_samples = 30
    df = pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temp_mean": [25.0 + i * 0.5 for i in range(n_samples)],
        "humidity": [50.0 + i for i in range(n_samples)],
        "ed_visits_heat": [100 + i for i in range(n_samples)],
    })
    df.loc[0, "ed_visits_heat"] = None
    return df


class TestMinimalDataset:
    """Tests for minimal dataset requirements."""

    def test_minimal_dataset_size(self, minimal_training_data):
        """Test that minimal dataset works."""
        pipeline = HeatShieldPipeline()

        # Should handle minimal dataset
        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)

        assert len(df_processed) == len(minimal_training_data)
        assert pipeline.fitted

    def test_minimal_dataset_features(self, minimal_training_data):
        """Test that features are created with minimal dataset."""
        pipeline = HeatShieldPipeline()

        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)
        feature_cols = pipeline.get_feature_columns()

        # Should have key features
        assert len(feature_cols) > 0

        # Lag features may have many NaN but should be created
        lag_cols = [c for c in feature_cols if "lag" in c]
        assert len(lag_cols) > 0

    def test_minimal_dataset_rolling(self, minimal_training_data):
        """Test rolling features with minimal dataset."""
        pipeline = HeatShieldPipeline()

        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)

        # Rolling features with window 3 should have NaN for first 2 rows
        rolling_3 = df_processed["ed_visits_rolling_mean_3"]
        assert rolling_3.isna().sum() >= 2


class TestMissingWeatherData:
    """Tests for handling missing weather data."""

    def test_missing_weather_strategy_mean(self, data_with_weather_gaps):
        """Test mean imputation for missing weather data."""
        pipeline = HeatShieldPipeline()

        df_processed, stats = pipeline.prepare_training_data(data_with_weather_gaps)

        # Check that missing values were imputed
        assert df_processed["temp_mean"].notna().all()

    def test_missing_weather_with_target(self, data_with_weather_gaps):
        """Test that missing weather doesn't affect target validation."""
        pipeline = HeatShieldPipeline()

        # Should pass target validation (missing weather is OK)
        is_valid, summary = pipeline.validate_training_data(data_with_weather_gaps)
        assert is_valid

    def test_missing_all_weather_features(self):
        """Test handling when all weather features are missing."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-06-01", periods=10, freq="D"),
            "ed_visits_heat": [100 + i for i in range(10)],
        })

        pipeline = HeatShieldPipeline()

        # Should work but without weather features
        df_processed, stats = pipeline.prepare_training_data(df)
        feature_cols = pipeline.get_feature_columns()

        # Should have calendar and other features
        assert len(feature_cols) > 0


class TestMissingTargetData:
    """Tests for handling missing target data."""

    def test_missing_target_error(self, data_with_missing_target):
        """Test that missing target values cause an error."""
        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(data_with_missing_target)

        # Should fail target validation
        assert not is_valid
        assert any("missing" in e.get("message", "").lower() for e in summary["errors"])

    def test_missing_target_imputation_not_allowed(self, data_with_missing_target):
        """Test that missing targets are never imputed."""
        pipeline = HeatShieldPipeline()

        # Should raise error during validation
        with pytest.raises(ValueError, match="missing target"):
            pipeline.prepare_training_data(data_with_missing_target)


class TestDataQuality:
    """Tests for data quality validation."""

    def test_negative_targets_error(self):
        """Test that negative target values cause an error."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-06-01", periods=10, freq="D"),
            "temp_mean": [25.0] * 10,
            "humidity": [50.0] * 10,
            "ed_visits_heat": [-5] * 10,  # Negative!
        })

        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(df)

        assert not is_valid
        assert any("negative" in e.get("message", "").lower() for e in summary["errors"])

    def test_valid_non_negative_targets(self):
        """Test that zero and positive targets are valid."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-06-01", periods=10, freq="D"),
            "temp_mean": [25.0] * 10,
            "humidity": [50.0] * 10,
            "ed_visits_heat": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45],
        })

        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(df)

        assert is_valid


class TestDateHandling:
    """Tests for date handling and ordering."""

    def test_unordered_dates_validation(self):
        """Test that unordered dates are detected."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-06-01", periods=10, freq="D"),
            "temp_mean": [25.0] * 10,
            "humidity": [50.0] * 10,
            "ed_visits_heat": list(range(10)),
        })
        # Shuffle to create unordered data
        df = df.sample(frac=1)

        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(df)

        assert not is_valid
        assert any("order" in str(e).lower() for e in summary["errors"])

    def test_date_sorting_in_pipeline(self, minimal_training_data):
        """Test that pipeline sorts data by date."""
        pipeline = HeatShieldPipeline()

        df_processed, _ = pipeline.prepare_training_data(minimal_training_data)

        dates = pd.to_datetime(df_processed["date"])
        assert dates.is_monotonic_increasing


class TestFeatureEngineeringWithMinimalData:
    """Tests for feature engineering with minimal data."""

    def test_lag_features_with_minimal_data(self, minimal_training_data):
        """Test lag feature creation with minimal data."""
        pipeline = HeatShieldPipeline()

        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)

        # Lag 7 should have 7 NaN values
        lag_7 = df_processed["ed_visits_lag_7"]
        assert lag_7.isna().sum() >= 7

    def test_rolling_features_with_minimal_data(self, minimal_training_data):
        """Test rolling feature creation with minimal data."""
        pipeline = HeatShieldPipeline()

        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)

        # Rolling mean 7 should have 6 NaN values (first 6 rows)
        rolling_7 = df_processed["ed_visits_rolling_mean_7"]
        assert rolling_7.isna().sum() >= 6


class TestTrainingDataSchema:
    """Tests for training data schema compliance."""

    def test_schema_compliance(self, minimal_training_data):
        """Test that training data meets schema requirements."""
        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.validate_training_data(minimal_training_data)

        assert is_valid, f"Data should be valid: {summary}"

    def test_schema_validation_summary(self, minimal_training_data):
        """Test that validation summary is complete."""
        pipeline = HeatShieldPipeline()

        is_valid, summary = pipeline.prepare_training_data(minimal_training_data)

        assert "created_at" in summary
        assert "feature_columns" in summary
        assert "feature_engineer_stats" in summary


class TestIntegration:
    """Integration tests for training data pipeline."""

    def test_end_to_end_training_pipeline(self, minimal_training_data, tmp_path):
        """Test end-to-end training pipeline."""
        pipeline = HeatShieldPipeline(
            data_dir=str(tmp_path / "data"),
            reports_dir=str(tmp_path / "reports"),
        )

        # Prepare training data
        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)

        # Verify output
        assert len(df_processed) > 0
        assert pipeline.fitted
        assert len(pipeline.get_feature_columns()) > 0

        # Generate schema
        schema = pipeline.generate_dataset_schema()
        assert schema["target"]["name"] == settings.target_column
        assert len(schema["input_columns"]) > 0

    def test_training_data_round_trip(self, minimal_training_data, tmp_path):
        """Test training data round trip (prepare -> save -> load)."""
        import json

        pipeline = HeatShieldPipeline(
            reports_dir=str(tmp_path / "reports"),
        )

        # Prepare data
        df_processed, stats = pipeline.prepare_training_data(minimal_training_data)

        # Save stats
        stats_path = pipeline.save_transformation_stats()
        assert stats_path.exists()

        # Load and verify
        with open(stats_path) as f:
            loaded_stats = json.load(f)

        assert "feature_columns" in loaded_stats
        assert loaded_stats["feature_columns"] == pipeline.get_feature_columns()
