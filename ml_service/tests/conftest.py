"""Shared pytest fixtures for ml_service tests."""

import sys
from pathlib import Path

# Make src.* importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor


@pytest.fixture
def sample_df():
    """30-row weather + target DataFrame matching the training schema."""
    n = 30
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "date":               pd.date_range("2024-06-01", periods=n, freq="D"),
        "tmax_c":             rng.uniform(18, 38, n),
        "tmin_c":             rng.uniform(10, 22, n),
        "humidity_pct":       rng.uniform(40, 90, n),
        "heat_index_c":       rng.uniform(18, 42, n),
        "uv_index":           rng.uniform(0, 10, n),
        "pm25_ugm3":          rng.uniform(2, 20, n),
        "ozone_ugm3":         rng.uniform(20, 80, n),
        "warm_night_flag":    rng.integers(0, 2, n).astype(float),
        "consecutive_hot_days": rng.integers(0, 10, n).astype(float),
        "heatwave_flag":      rng.integers(0, 2, n).astype(float),
        "day_of_week":        rng.integers(0, 7, n),
        "is_bank_holiday":    rng.integers(0, 2, n),
        "general_acute_beds": rng.integers(300, 900, n),
        "icu_beds":           rng.integers(10, 50, n),
        "ambulances_available": rng.integers(10, 40, n),
        "baseline_staff_per_shift": rng.integers(200, 700, n),
        "bed_occupancy_pct":  rng.uniform(60, 98, n),
        "pct_pop_over_65":    rng.uniform(10, 30, n),
        "pct_pop_under_5":    rng.uniform(3, 8, n),
        "imd_deprivation_decile": rng.integers(1, 11, n),
        "green_space_pct":    rng.uniform(5, 50, n),
        "ac_cooled_wards_pct": rng.uniform(10, 80, n),
        "ae_attendances":     rng.integers(60, 250, n).astype(float),
    })


@pytest.fixture
def tiny_model():
    """A minimal trained sklearn model for prediction tests."""
    rng = np.random.default_rng(0)
    X = rng.uniform(0, 1, (50, 2))
    y = rng.uniform(60, 200, 50)
    m = GradientBoostingRegressor(n_estimators=5, random_state=0)
    m.fit(X, y)
    return m
