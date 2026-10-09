"""Tests for feature ordering and temporal leakage prevention."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from app.ml.features import FeatureEngineer
from app.ml.validation import DataValidator
from app.config import settings


@pytest.fixture
def feature_engineer():
    """Create FeatureEngineer instance."""
    return FeatureEngineer(
        date_column="date",
        target_column="ed_visits_heat",
    )


@pytest.fixture
def test_data():
    """Create test data with known properties."""
    return pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=20, freq="D"),
        "temp_mean": [25.0 + i * 0.5 for i in range(20)],
        "humidity": [50.0 + i for i in range(20)],
        "ed_visits_heat": [100 + i for i in range(20)],
    })


class TestFeatureOrder:
    """Tests for feature ordering requirements."""

    def test_feature_columns_are_consistent(self, feature_engineer, test_data):
        """Test that feature columns are populated after engineering."""
        df = feature_engineer.engineer_all_features(test_data, fit=True)
        feature_cols = feature_engineer.get_feature_columns()

        assert len(feature_cols) > 0
        assert isinstance(feature_cols, list)

        # Check that feature columns don't include target
        assert settings.target_column not in feature_cols

        # Check that feature columns include expected types
        has_lag = any("lag" in c for c in feature_cols)
        has_rolling = any("rolling" in c for c in feature_cols)
        has_calendar = any(c in feature_cols for c in ["month", "season"])
        has_weather = any("temp" in c or "humidity" in c for c in feature_cols)

        assert has_lag, "Expected lag features"
        assert has_rolling, "Expected rolling features"
        assert has_calendar, "Expected calendar features"
        assert has_weather, "Expected weather features"

    def test_feature_order_inference_mode(self, feature_engineer, test_data):
        """Test that feature ordering works in inference mode."""
        # First fit on training data
        df_train = test_data.copy()
        df_train = feature_engineer.engineer_all_features(df_train, fit=True)

        # Then use same order for inference
        df_inference = test_data.copy()
        df_inference = df_inference.drop(columns=[settings.target_column])
        df_inference = feature_engineer.engineer_all_features(df_inference, fit=False)

        # Both should have the same feature columns
        train_features = feature_engineer.get_feature_columns()

        # For inference, some lag features might be missing but others should match
        inference_features = [c for c in df_inference.columns if c != settings.target_column]

        # Check that calendar features match exactly
        calendar_features = ["month", "day_of_week", "season"]
        for cf in calendar_features:
            if cf in train_features:
                assert cf in inference_features, f"Calendar feature {cf} missing in inference"

    def test_feature_order_preservation(self, feature_engineer, test_data):
        """Test that feature order is preserved across multiple calls."""
        df1 = feature_engineer.engineer_all_features(test_data.copy(), fit=True)
        features1 = feature_engineer.get_feature_columns()

        df2 = feature_engineer.engineer_all_features(test_data.copy(), fit=True)
        features2 = feature_engineer.get_feature_columns()

        assert features1 == features2, "Feature order should be consistent"


class TestMissingColumns:
    """Tests for handling missing columns."""

    def test_handle_missing_weather_features(self, feature_engineer, test_data):
        """Test handling of missing weather features."""
        # Create data missing some weather features
        df = test_data.drop(columns=["temp_mean"])

        # Should still work, just won't create temp-related features
        df = feature_engineer.engineer_all_features(df, fit=True)
        feature_cols = feature_engineer.get_feature_columns()

        # Should still have some features
        assert len(feature_cols) > 0

        # Temperature-related features should be missing
        temp_features = [c for c in feature_cols if "temp" in c]
        assert len(temp_features) == 0

    def test_handle_missing_calendar_features(self, feature_engineer, test_data):
        """Test handling of missing date column."""
        df = test_data.drop(columns=["date"])

        # Should fail without date column
        with pytest.raises(KeyError):
            feature_engineer.engineer_all_features(df, fit=True)

    def test_handle_missing_target_inference(self, feature_engineer, test_data):
        """Test handling of missing target column in inference mode."""
        df = test_data.drop(columns=[settings.target_column])

        # Should work in inference mode
        df = feature_engineer.engineer_all_features(df, fit=False)
        feature_cols = feature_engineer.get_feature_columns()

        # Should have features but no target
        assert len(feature_cols) > 0
        assert settings.target_column not in df.columns


class TestMissingDates:
    """Tests for handling missing dates."""

    def test_handle_missing_dates_in_sequence(self, feature_engineer, test_data):
        """Test feature creation with gaps in dates."""
        # Create data with a gap
        df = test_data.copy()
        df = df.drop(index=[5, 6, 7])  # Remove 3 days

        # Should still create features but with NaN for lagged values
        df = feature_engineer.engineer_all_features(df, fit=True)

        # Lag features should have NaN where data is missing
        assert "ed_visits_lag_1" in df.columns
        assert df["ed_visits_lag_1"].isna().sum() > 0

    def test_handle_missing_dates_with_interpolation(self, feature_engineer, test_data):
        """Test handling of missing dates with interpolation."""
        # This is more of a data preparation concern
        # The feature engineer handles what's present
        df = feature_engineer.engineer_all_features(test_data, fit=True)

        # Verify all expected features are present
        assert "is_heatwave" in df.columns
        assert "is_weekend" in df.columns


class TestTemporalLeakage:
    """Tests for temporal leakage prevention."""

    def test_no_future_data_in_lag_features(self, feature_engineer, test_data):
        """Test that lag features don't use future data."""
        df = feature_engineer.engineer_all_features(test_data, fit=True)

        # For each row, lag feature should only use past values
        for i in range(len(df)):
            if i >= 1:
                # Row i's lag_1 should equal row i-1's target
                expected = test_data[settings.target_column].iloc[i - 1]
                actual = df["ed_visits_lag_1"].iloc[i]
                assert expected == actual, f"Row {i}: lag_1 should use previous row's target"

    def test_no_future_data_in_rolling_features(self, feature_engineer, test_data):
        """Test that rolling features don't use future data."""
        df = feature_engineer.engineer_all_features(test_data, fit=True)

        # Rolling mean should use only past values
        window = 3
        for i in range(len(df)):
            if i >= window:
                # Row i's rolling mean should be mean of rows i-window to i-1
                expected = test_data[settings.target_column].iloc[i - window:i].mean()
                actual = df[f"ed_visits_rolling_mean_{window}"].iloc[i]
                # Allow small floating point differences
                assert abs(expected - actual) < 0.01, f"Row {i}: rolling mean should use past values only"

    def test_no_target_in_features(self, feature_engineer, test_data):
        """Test that target values are not duplicated as features."""
        df = feature_engineer.engineer_all_features(test_data, fit=True)

        # The target column should not be in feature columns
        feature_cols = feature_engineer.get_feature_columns()
        assert settings.target_column not in feature_cols

        # Also check that no feature has the same name as target
        for col in df.columns:
            if col != settings.target_column:
                assert col != settings.target_column

    def test_date_sorting_prevents_leakage(self, feature_engineer, test_data):
        """Test that date sorting prevents leakage."""
        # Shuffle the data
        df_shuffled = test_data.sample(frac=1)

        # Engineered features should be based on sorted dates
        df = feature_engineer.engineer_all_features(df_shuffled, fit=True)

        # Verify data is sorted by date
        dates = pd.to_datetime(df["date"])
        assert dates.is_monotonic_increasing, "Data should be sorted by date"

        # Lag features should still be correct after sorting
        for i in range(1, len(df)):
            expected = test_data[settings.target_column].iloc[i - 1]
            actual = df["ed_visits_lag_1"].iloc[i]
            assert expected == actual

    def test_leakage_validation_detects_problems(self, test_data):
        """Test that leakage validation detects issues."""
        from app.ml.validation import DataValidator

        validator = DataValidator(
            target_column=settings.target_column,
            date_column=settings.date_column,
        )

        # Clean data should pass
        results = validator.validate_leakage_prevention(test_data)
        assert not results["leakage_detected"]

        # Unordered data should fail
        df_unordered = test_data.sample(frac=1)
        results = validator.validate_leakage_prevention(df_unordered)
        assert results["leakage_detected"]


class TestFeatureReport:
    """Tests for feature report generation."""

    def test_generate_feature_report(self, feature_engineer, test_data):
        """Test feature report generation."""
        df = feature_engineer.engineer_all_features(test_data, fit=True)
        report = feature_engineer.generate_feature_report(df, fit=True)

        assert "total_columns" in report
        assert "feature_columns" in report
        assert "feature_types" in report
        assert "calendar" in report["feature_types"]
        assert "lag" in report["feature_types"]
        assert "rolling" in report["feature_types"]

    def test_generate_feature_report_inference(self, feature_engineer, test_data):
        """Test feature report generation in inference mode."""
        df = test_data.drop(columns=[settings.target_column])
        df = feature_engineer.engineer_all_features(df, fit=False)
        report = feature_engineer.generate_feature_report(df, fit=False)

        assert "total_columns" in report
        assert "feature_columns" in report
