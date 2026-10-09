"""Tests for minimal dataset requirements and training data validation."""

import numpy as np
import pandas as pd
import pytest
from src.core.pipeline import HeatShieldPipeline


def _make_df(n=95, seed=42):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "date":           pd.date_range("2024-06-01", periods=n, freq="D"),
        "tmax_c":         rng.uniform(18, 38, n),
        "tmin_c":         rng.uniform(10, 22, n),
        "humidity_pct":   rng.uniform(40, 90, n),
        "heat_index_c":   rng.uniform(18, 42, n),
        "uv_index":       rng.uniform(0, 10, n),
        "pm25_ugm3":      rng.uniform(2, 20, n),
        "ozone_ugm3":     rng.uniform(20, 80, n),
        "warm_night_flag": rng.integers(0, 2, n).astype(float),
        "consecutive_hot_days": rng.integers(0, 5, n).astype(float),
        "heatwave_flag":  rng.integers(0, 2, n).astype(float),
        "day_of_week":    rng.integers(0, 7, n),
        "is_bank_holiday": rng.integers(0, 2, n),
        "general_acute_beds": rng.integers(300, 900, n),
        "icu_beds":        rng.integers(10, 50, n),
        "ambulances_available": rng.integers(10, 40, n),
        "baseline_staff_per_shift": rng.integers(200, 700, n),
        "bed_occupancy_pct": rng.uniform(60, 98, n),
        "pct_pop_over_65": rng.uniform(10, 30, n),
        "pct_pop_under_5": rng.uniform(3, 8, n),
        "imd_deprivation_decile": rng.integers(1, 11, n),
        "green_space_pct": rng.uniform(5, 50, n),
        "ac_cooled_wards_pct": rng.uniform(10, 80, n),
        "ae_attendances": rng.integers(60, 250, n).astype(float),
    })


def test_minimal_dataset_works():
    p = HeatShieldPipeline()
    df = _make_df(95)
    out, stats = p.prepare_training_data(df)
    assert p.fitted
    assert len(out) == len(df)


def test_minimal_dataset_has_lag_features():
    p = HeatShieldPipeline()
    out, stats = p.prepare_training_data(_make_df(95))
    lag_cols = [c for c in p.get_feature_columns() if "lag" in c]
    assert len(lag_cols) > 0


def test_missing_weather_handled():
    df = _make_df(30)
    df.loc[5:7, "tmax_c"] = None   # introduce missing values
    p = HeatShieldPipeline()
    out, _ = p.prepare_training_data(df)
    assert out["tmax_c"].isnull().sum() == 0  # imputed


def test_missing_target_raises():
    df = _make_df(30)
    df.loc[0, "ae_attendances"] = None
    p = HeatShieldPipeline()
    with pytest.raises(ValueError):
        p.prepare_training_data(df)


def test_large_dataset_works():
    p = HeatShieldPipeline()
    out, stats = p.prepare_training_data(_make_df(500))
    assert p.fitted
    assert len(p.get_feature_columns()) > 5
