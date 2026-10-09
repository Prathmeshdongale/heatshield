"""Tests for feature engineering."""

import pandas as pd
import pytest
from src.core.features import FeatureEngineer, validate_leakage_prevention


def test_calendar_features_created(sample_df):
    fe = FeatureEngineer()
    df = fe.create_calendar_features(sample_df)
    for col in ("month", "day_of_week", "is_weekend", "season"):
        assert col in df.columns, f"Missing {col}"


def test_temperature_features_created(sample_df):
    fe = FeatureEngineer(date_column="date")
    df = fe.create_calendar_features(sample_df)
    # Add temp_mean alias so the feature engineer can find it
    df["temp_mean"] = df["tmax_c"]
    df = fe.create_temperature_features(df)
    assert "is_heatwave" in df.columns
    assert "is_extreme_heat" in df.columns


def test_lag_features_shift(sample_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    df = fe.create_lag_features(sample_df, fit=True)
    # Lag-1 at row i == target at row i-1
    assert df["ae_attendances_lag_1"].iloc[1] == sample_df["ae_attendances"].iloc[0]


def test_rolling_features_no_current_day(sample_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    df = fe.create_rolling_features(sample_df, fit=True)
    assert "ae_attendances_rolling_mean_3" in df.columns


def test_engineer_all_features_fit(sample_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    df = fe.engineer_all_features(sample_df, fit=True)
    assert fe.fitted
    assert len(fe.feature_columns) > 0
    assert "ae_attendances" not in fe.feature_columns


def test_no_leakage_in_engineered_data(sample_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    df = fe.engineer_all_features(sample_df, fit=True)
    result = validate_leakage_prevention(df)
    assert not result["leakage_detected"], result["issues"]
