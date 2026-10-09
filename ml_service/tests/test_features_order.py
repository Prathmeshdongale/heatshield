"""Tests for feature ordering and leakage prevention."""

import numpy as np
import pandas as pd
import pytest
from src.core.features import FeatureEngineer, validate_leakage_prevention
from src.config import settings


@pytest.fixture
def ordered_df():
    n = 25
    rng = np.random.default_rng(7)
    return pd.DataFrame({
        "date":           pd.date_range("2024-06-01", periods=n, freq="D"),
        "tmax_c":         rng.uniform(20, 38, n),
        "tmin_c":         rng.uniform(10, 22, n),
        "humidity_pct":   rng.uniform(40, 80, n),
        "ae_attendances": rng.integers(70, 200, n).astype(float),
    })


def test_feature_columns_populated(ordered_df):
    fe = FeatureEngineer()
    fe.engineer_all_features(ordered_df, fit=True)
    assert len(fe.get_feature_columns()) > 0


def test_target_not_in_feature_columns(ordered_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    fe.engineer_all_features(ordered_df, fit=True)
    assert settings.target_column not in fe.get_feature_columns()


def test_lag_features_present(ordered_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    fe.engineer_all_features(ordered_df, fit=True)
    lag_cols = [c for c in fe.get_feature_columns() if "lag" in c]
    assert len(lag_cols) > 0, "Expected at least one lag feature"


def test_rolling_features_present(ordered_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    fe.engineer_all_features(ordered_df, fit=True)
    roll_cols = [c for c in fe.get_feature_columns() if "rolling" in c]
    assert len(roll_cols) > 0, "Expected at least one rolling feature"


def test_consistent_feature_columns_train_vs_inference(ordered_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    df_train = fe.engineer_all_features(ordered_df, fit=True)
    train_cols = fe.get_feature_columns()

    # Inference: same data minus target column
    df_inf = ordered_df.drop(columns=["ae_attendances"])
    df_inf_out = fe.engineer_all_features(df_inf, fit=False)
    inf_cols = [c for c in df_inf_out.columns if c != "ae_attendances"]
    # All training features except target/lag/rolling should be in inference output
    weather_and_cal = [c for c in train_cols if "lag" not in c and "rolling" not in c]
    for col in weather_and_cal:
        assert col in df_inf_out.columns, f"Missing in inference: {col}"


def test_no_leakage_after_engineering(ordered_df):
    fe = FeatureEngineer(target_column="ae_attendances")
    df = fe.engineer_all_features(ordered_df, fit=True)
    result = validate_leakage_prevention(df, target_column="ae_attendances")
    assert not result["leakage_detected"], result["issues"]
