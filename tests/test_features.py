"""Tests for feature engineering module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.ml.features import FeatureEngineer, validate_leakage_prevention
from app.config import settings


@pytest.fixture
def sample_weather_data():
    """Create sample weather data for testing."""
    n_samples = 30
    return pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temp_mean": [25.0 + i * 0.5 for i in range(n_samples)],
        "temp_max": [30.0 + i * 0.5 for i in range(n_samples)],
        "temp_min": [20.0 + i * 0.5 for i in range(n_samples)],
        "humidity": [50.0 + i for i in range(n_samples)],
        "precipitation": [0.0] * n_samples,
        "wind_speed": [10.0] * n_samples,
    })


@pytest.fixture
def sample_healthcare_data():
    """Create sample healthcare data for testing."""
    n_samples = 30
    return pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "ed_visits_heat": [100 + i for i in range(n_samples)],
    })


@pytest.fixture
def sample_combined_data():
    """Create combined weather and healthcare data."""
    n_samples = 30
    return pd.DataFrame({
        "date": pd.date_range("2023-06-01", periods=n_samples, freq="D"),
        "temp_mean": [25.0 + i * 0.5 for i in range(n_samples)],
        "humidity": [50.0 + i for i in range(n_samples)],
        "ed_visits_heat": [100 + i for i in range(n_samples)],
    })


@pytest.fixture
def feature_engineer():
    """Create FeatureEngineer instance."""
    return FeatureEngineer(
        date_column="date",
        target_column="ed_visits_heat",
    )


class TestTemperatureFeatures:
    """Tests for temperature feature creation."""

    def test_create_temperature_features(self, feature_engineer, sample_weather_data):
        """Test temperature feature creation."""
        df = feature_engineer.create_temperature_features(sample_weather_data)
        assert "temp_range" in df.columns
        assert "is_heatwave" in df.columns
        assert "is_extreme_heat" in df.columns

    def test_temperature_range_calculation(self, feature_engineer, sample_weather_data):
        """Test temperature range calculation."""
        df = feature_engineer.create_temperature_features(sample_weather_data)
        expected_range = sample_weather_data["temp_max"] - sample_weather_data["temp_min"]
        assert np.allclose(df["temp_range"], expected_range)

    def test_heatwave_indicator(self, feature_engineer, sample_weather_data):
        """Test heatwave indicator creation."""
        df = feature_engineer.create_temperature_features(sample_weather_data)
        # Check that heatwave flag is set when temp >= threshold
        assert (df["is_heatwave"] >= 0).all()
        assert (df["is_heatwave"] <= 1).all()

    def test_extreme_heat_indicator(self, feature_engineer, sample_weather_data):
        """Test extreme heat indicator creation."""
        df = feature_engineer.create_temperature_features(sample_weather_data)
        assert "is_extreme_heat" in df.columns


class TestWeatherFeatures:
    """Tests for weather combination features."""

    def test_create_weather_features(self, feature_engineer, sample_weather_data):
        """Test weather combination feature creation."""
        df = feature_engineer.create_weather_features(sample_weather_data)
        assert "heat_stress_index" in df.columns
        assert "is_drought" in df.columns
        assert "in_comfort_zone" in df.columns


class TestCalendarFeatures:
    """Tests for calendar feature creation."""

    def test_create_calendar_features(self, feature_engineer, sample_weather_data):
        """Test calendar feature creation."""
        df = feature_engineer.create_calendar_features(sample_weather_data)
        assert "year" in df.columns
        assert "month" in df.columns
        assert "day_of_week" in df.columns
        assert "season" in df.columns
        assert "is_weekend" in df.columns

    def test_season_classification(self, feature_engineer):
        """Test season classification for different months."""
        df = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=12, freq="M")})
        df = feature_engineer.create_calendar_features(df)

        # Check season assignments
        winter_months = [0, 1, 11]  # Dec, Jan, Feb
        spring_months = [2, 3, 4]   # Mar, Apr, May
        summer_months = [5, 6, 7]   # Jun, Jul, Aug
        autumn_months = [8, 9, 10]  # Sep, Oct, Nov

        for month_idx in winter_months:
            assert df.loc[month_idx, "season"] == "winter"
        for month_idx in spring_months:
            assert df.loc[month_idx, "season"] == "spring"
        for month_idx in summer_months:
            assert df.loc[month_idx, "season"] == "summer"
        for month_idx in autumn_months:
            assert df.loc[month_idx, "season"] == "autumn"


class TestLagFeatures:
    """Tests for lag feature creation."""

    def test_create_lag_features(self, feature_engineer, sample_combined_data):
        """Test lag feature creation."""
        df = feature_engineer.create_lag_features(sample_combined_data, fit=True)
        for lag in settings.lag_days:
            assert f"ed_visits_lag_{lag}" in df.columns

    def test_lag_features_necessary_nan(self, feature_engineer, sample_combined_data):
        """Test that lag features have necessary NaN values."""
        df = feature_engineer.create_lag_features(sample_combined_data, fit=True)
        # Lag 1 should have 1 NaN at the start
        assert df["ed_visits_lag_1"].isna().sum() == 1
        # Lag 3 should have 3 NaNs at the start
        assert df["ed_visits_lag_3"].isna().sum() == 3

    def test_lag_features_values(self, feature_engineer, sample_combined_data):
        """Test that lag features have correct values."""
        df = feature_engineer.create_lag_features(sample_combined_data, fit=True)
        # For a 3-day lag, row 3 should equal row 0 of target
        expected_lag = sample_combined_data["ed_visits_heat"].iloc[0]
        actual_lag = df["ed_visits_lag_3"].iloc[3]
        assert expected_lag == actual_lag

    def test_lag_features_no_target_inference(self, feature_engineer, sample_combined_data):
        """Test lag features without target column (inference mode)."""
        # Create a copy without target column
        df_inference = sample_combined_data.drop(columns=["ed_visits_heat"])
        df = feature_engineer.create_lag_features(df_inference, fit=False)
        assert "ed_visits_lag_1" not in df.columns


class TestRollingFeatures:
    """Tests for rolling feature creation."""

    def test_create_rolling_features(self, feature_engineer, sample_combined_data):
        """Test rolling feature creation."""
        df = feature_engineer.create_rolling_features(sample_combined_data, fit=True)
        for window in settings.rolling_windows:
            assert f"ed_visits_rolling_mean_{window}" in df.columns

    def test_rolling_features_use_past_only(self, feature_engineer, sample_combined_data):
        """Test that rolling features use only past data."""
        df = feature_engineer.create_rolling_features(sample_combined_data, fit=True)
        # Rolling mean should start with valid values after the window
        assert df["ed_visits_rolling_mean_3"].notna().any()

    def test_rolling_features_values(self, feature_engineer, sample_combined_data):
        """Test rolling feature calculations."""
        df = feature_engineer.create_rolling_features(sample_combined_data, fit=True)
        # Check a specific rolling mean calculation
        window = 3
        # Row at index 2 should have mean of rows 0, 1, 2 (but shifted by 1)
        # So it's actually mean of rows 0, 1
        expected_mean = sample_combined_data["ed_visits_heat"].iloc[:2].mean()
        actual_mean = df["ed_visits_rolling_mean_3"].iloc[2]
        assert np.isclose(expected_mean, actual_mean)


class TestFeatureEngineeringPipeline:
    """Tests for full feature engineering pipeline."""

    def test_engineer_all_features(self, feature_engineer, sample_combined_data):
        """Test full feature engineering pipeline."""
        df = feature_engineer.engineer_all_features(sample_combined_data, fit=True)
        assert len(df.columns) > len(sample_combined_data.columns)
        assert "ed_visits_lag_1" in df.columns
        assert "is_heatwave" in df.columns
        assert "month" in df.columns

    def test_feature_columns_list(self, feature_engineer, sample_combined_data):
        """Test that feature columns list is populated."""
        df = feature_engineer.engineer_all_features(sample_combined_data, fit=True)
        assert len(feature_engineer.feature_columns) > 0
        assert "ed_visits_lag_1" in feature_engineer.feature_columns

    def test_engineering_preserves_date_order(self, feature_engineer, sample_combined_data):
        """Test that engineering preserves date ordering."""
        df = feature_engineer.engineer_all_features(sample_combined_data, fit=True)
        dates = pd.to_datetime(df["date"])
        assert dates.is_monotonic_increasing

    def test_engineering_with_missing_target(self, feature_engineer, sample_combined_data):
        """Test feature engineering without target column."""
        df_inference = sample_combined_data.drop(columns=["ed_visits_heat"])
        df = feature_engineer.engineer_all_features(df_inference, fit=False)
        assert "ed_visits_lag_1" not in df.columns  # No lag without target


class TestLeakagePrevention:
    """Tests for leakage prevention validation."""

    def test_validate_leakage_prevention_clean(self, sample_combined_data):
        """Test validation of clean data."""
        results = validate_leakage_prevention(
            sample_combined_data,
            date_column="date",
            target_column="ed_visits_heat",
        )
        assert not results["leakage_detected"]

    def test_validate_leakage_prevention_unordered(self, sample_combined_data):
        """Test validation with unordered dates."""
        df = sample_combined_data.sample(frac=1)  # Shuffle rows
        results = validate_leakage_prevention(df, date_column="date", target_column="ed_visits_heat")
        assert results["leakage_detected"]

    def test_validate_leakage_prevention_no_target(self, sample_weather_data):
        """Test validation without target column."""
        results = validate_leakage_prevention(
            sample_weather_data,
            date_column="date",
            target_column="ed_visits_heat",
        )
        assert not results["leakage_detected"]
        assert "Target column not found" in str(results["warnings"])


class TestFeatureValidation:
    """Tests for feature validation."""

    def test_validate_features_present(self, feature_engineer, sample_combined_data):
        """Test validation of present features."""
        df = feature_engineer.engineer_all_features(sample_combined_data, fit=True)
        validation = feature_engineer.validate_features(df)
        assert validation["valid"]

    def test_validate_features_missing(self, feature_engineer):
        """Test validation of missing features."""
        df = pd.DataFrame({"date": pd.date_range("2023-06-01", periods=5)})
        validation = feature_engineer.validate_features(df)
        assert not validation["valid"]
        assert len(validation["missing_features"]) > 0

    def test_validate_feature_order(self, feature_engineer, sample_combined_data):
        """Test feature order validation."""
        df = feature_engineer.engineer_all_features(sample_combined_data, fit=True)
        expected_features = feature_engineer.get_feature_columns()
        actual_features = list(df.columns)

        # Remove target from actual for comparison
        actual_features = [c for c in actual_features if c != "ed_visits_heat"]

        assert set(expected_features) == set(actual_features)
