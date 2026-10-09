"""Tests for data validation module."""

import pytest
import pandas as pd
import numpy as np

from app.ml.validation import DataValidator
from app.config import settings


@pytest.fixture
def validator():
    """Create DataValidator instance."""
    return DataValidator(
        target_column=settings.target_column,
        date_column=settings.date_column,
    )


@pytest.fixture
def valid_weather_data():
    """Create valid weather data DataFrame."""
    return pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=10, freq="D"),
        "temp_mean": [20.0 + i for i in range(10)],
        "humidity": [50.0 + i for i in range(10)],
        "temp_max": [25.0 + i for i in range(10)],
        "temp_min": [15.0 + i for i in range(10)],
    })


@pytest.fixture
def valid_healthcare_data():
    """Create valid healthcare data DataFrame."""
    return pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=10, freq="D"),
        "ed_visits_heat": [100 + i for i in range(10)],
    })


@pytest.fixture
def data_with_missing_targets():
    """Create healthcare data with missing target values."""
    df = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=10, freq="D"),
        "ed_visits_heat": [100 + i for i in range(10)],
    })
    df.loc[0, "ed_visits_heat"] = None
    return df


@pytest.fixture
def unordered_data():
    """Create unordered data for leakage testing."""
    df = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=10, freq="D"),
        "ed_visits_heat": list(range(10)),
    })
    return df.sample(frac=1)  # Shuffle rows


class TestDataValidation:
    """Tests for basic data validation."""

    def test_validate_weather_data_valid(self, validator, valid_weather_data):
        """Test validation of valid weather data."""
        is_valid, errors, warnings = validator.validate_weather_data(valid_weather_data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_weather_data_missing_columns(self, validator, valid_weather_data):
        """Test validation with missing columns."""
        df = valid_weather_data.drop(columns=["temp_mean"])
        is_valid, errors, warnings = validator.validate_weather_data(df)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_weather_data_null_values(self, validator, valid_weather_data):
        """Test validation with null values."""
        df = valid_weather_data.copy()
        df.loc[0, "temp_mean"] = None
        is_valid, errors, warnings = validator.validate_weather_data(df)
        assert is_valid  # Not an error, just a warning
        assert len(warnings) > 0


class TestTargetValidation:
    """Tests for target column validation."""

    def test_validate_target_valid(self, validator, valid_healthcare_data):
        """Test validation of valid target data."""
        is_valid, errors, warnings = validator.validate_target_column(valid_healthcare_data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_target_missing(self, validator):
        """Test validation with missing target column."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=10, freq="D"),
        })
        is_valid, errors, warnings = validator.validate_target_column(df)
        assert not is_valid
        assert len(errors) > 0
        assert "not found" in errors[0]["message"]

    def test_validate_target_null_values(self, validator, data_with_missing_targets):
        """Test validation with null target values."""
        is_valid, errors, warnings = validator.validate_target_column(data_with_missing_targets)
        assert not is_valid
        assert len(errors) > 0
        assert "missing" in errors[0]["message"].lower()

    def test_validate_target_negative_values(self, validator):
        """Test validation with negative target values."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=10, freq="D"),
            "ed_visits_heat": [-5] * 10,
        })
        is_valid, errors, warnings = validator.validate_target_column(df)
        assert not is_valid
        assert len(errors) > 0
        assert "negative" in errors[0]["message"].lower()


class TestLeakagePrevention:
    """Tests for leakage prevention validation."""

    def test_validate_leakage_clean_data(self, validator, valid_healthcare_data):
        """Test validation of clean data."""
        results = validator.validate_leakage_prevention(
            valid_healthcare_data,
            target_column="ed_visits_heat",
            date_column="date",
        )
        assert not results["leakage_detected"]
        assert len(results["checks_performed"]) > 0

    def test_validate_leakage_unordered_dates(self, validator, unordered_data):
        """Test validation with unordered dates."""
        results = validator.validate_leakage_prevention(
            unordered_data,
            target_column="ed_visits_heat",
            date_column="date",
        )
        assert results["leakage_detected"]
        assert any("ordering" in msg.lower() for msg in results["issues"])

    def test_validate_leakage_no_target(self, validator, valid_weather_data):
        """Test validation without target column."""
        results = validator.validate_leakage_prevention(
            valid_weather_data,
            target_column="ed_visits_heat",
            date_column="date",
        )
        assert not results["leakage_detected"]
        assert len(results["warnings"]) > 0

    def test_validate_leakage_with_lag_features(self, validator, valid_healthcare_data):
        """Test validation with lag features."""
        # Create a DataFrame with lag features
        df = valid_healthcare_data.copy()
        df["ed_visits_lag_1"] = df["ed_visits_heat"].shift(1)
        df["ed_visits_rolling_mean_3"] = df["ed_visits_heat"].shift(1).rolling(3).mean()

        results = validator.validate_leakage_prevention(
            df,
            target_column="ed_visits_heat",
            date_column="date",
            lag_features=["ed_visits_lag_1", "ed_visits_rolling_mean_3"],
        )
        assert not results["leakage_detected"]


class TestDateRangeValidation:
    """Tests for date range validation."""

    def test_validate_date_range_valid(self, validator, valid_healthcare_data):
        """Test validation of valid date range."""
        is_valid, errors, warnings = validator.validate_date_range(
            valid_healthcare_data,
            start_date=pd.Timestamp("2023-01-01"),
            end_date=pd.Timestamp("2023-01-31"),
        )
        assert is_valid
        assert len(errors) == 0

    def test_validate_date_range_early_start(self, validator, valid_healthcare_data):
        """Test validation with early start date."""
        is_valid, errors, warnings = validator.validate_date_range(
            valid_healthcare_data,
            start_date=pd.Timestamp("2022-12-01"),
        )
        assert not is_valid
        assert len(errors) > 0

    def test_validate_date_range_late_end(self, validator, valid_healthcare_data):
        """Test validation with late end date."""
        is_valid, errors, warnings = validator.validate_date_range(
            valid_healthcare_data,
            end_date=pd.Timestamp("2023-01-15"),
        )
        assert not is_valid
        assert len(errors) > 0


class TestFeatureOrderValidation:
    """Tests for feature order validation."""

    def test_validate_feature_order_valid(self, validator):
        """Test validation of correct feature order."""
        expected = ["feature1", "feature2", "feature3"]
        actual = ["feature1", "feature2", "feature3"]

        results = validator.validate_feature_order(expected, actual)
        assert results["order_valid"]
        assert len(results["missing_features"]) == 0
        assert len(results["extra_features"]) == 0

    def test_validate_feature_order_missing(self, validator):
        """Test validation with missing features."""
        expected = ["feature1", "feature2", "feature3"]
        actual = ["feature1", "feature2"]

        results = validator.validate_feature_order(expected, actual)
        assert not results["order_valid"]
        assert "feature3" in results["missing_features"]

    def test_validate_feature_order_extra(self, validator):
        """Test validation with extra features."""
        expected = ["feature1", "feature2"]
        actual = ["feature1", "feature2", "feature3"]

        results = validator.validate_feature_order(expected, actual)
        assert not results["order_valid"]
        assert "feature3" in results["extra_features"]

    def test_validate_feature_order_mismatch(self, validator):
        """Test validation with feature order mismatch."""
        expected = ["feature1", "feature2", "feature3"]
        actual = ["feature1", "feature3", "feature2"]

        results = validator.validate_feature_order(expected, actual)
        assert not results["order_valid"]
        assert len(results["order_mismatch"]) > 0


class TestDatasetCompleteness:
    """Tests for dataset completeness validation."""

    def test_validate_completeness_complete(self, validator):
        """Test validation of complete dataset."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=10, freq="D"),
        })
        expected_dates = pd.date_range("2023-01-01", periods=10, freq="D")

        results = validator.validate_dataset_completeness(df, expected_dates)
        assert results["complete"]
        assert len(results["missing_dates"]) == 0

    def test_validate_completeness_missing_dates(self, validator):
        """Test validation with missing dates."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=8, freq="D"),
        })
        expected_dates = pd.date_range("2023-01-01", periods=10, freq="D")

        results = validator.validate_dataset_completeness(df, expected_dates)
        assert not results["complete"]
        assert len(results["missing_dates"]) > 0

    def test_validate_completeness_no_date_column(self, validator):
        """Test validation without date column."""
        df = pd.DataFrame({
            "value": [1, 2, 3],
        })
        results = validator.validate_dataset_completeness(df)
        assert not results["complete"]
        assert len(results["missing_dates"]) > 0
