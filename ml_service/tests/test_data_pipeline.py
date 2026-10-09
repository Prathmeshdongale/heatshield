"""Tests for HeatShieldPipeline."""

import json
import numpy as np
import pandas as pd
import pytest
from src.core.pipeline import HeatShieldPipeline


@pytest.fixture
def pipeline_df():
    n = 50
    rng = np.random.default_rng(42)
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


def test_pipeline_directories_created(tmp_path):
    p = HeatShieldPipeline(
        data_dir=str(tmp_path / "data"),
        reports_dir=str(tmp_path / "reports"),
    )
    assert p.data_dir.exists()
    assert p.reports_dir.exists()


def test_pipeline_components_initialized(pipeline_df):
    p = HeatShieldPipeline()
    assert p.feature_engineer is not None
    assert p.preprocessor is not None
    assert p.validator is not None


def test_pipeline_fit(pipeline_df):
    p = HeatShieldPipeline()
    df_out, stats = p.prepare_training_data(pipeline_df)
    assert p.fitted
    assert len(df_out.columns) > len(pipeline_df.columns)
    assert "feature_columns" in stats


def test_pipeline_more_columns_after_fit(pipeline_df):
    p = HeatShieldPipeline()
    df_out, _ = p.prepare_training_data(pipeline_df)
    # Should have lag + rolling + calendar features
    assert len(p.get_feature_columns()) > 0


def test_pipeline_saves_stats(tmp_path, pipeline_df):
    p = HeatShieldPipeline(reports_dir=str(tmp_path))
    p.prepare_training_data(pipeline_df, save_stats=True)
    stats_file = tmp_path / "transformation_stats.json"
    assert stats_file.exists()
    with open(stats_file) as f:
        data = json.load(f)
    assert "feature_columns" in data
