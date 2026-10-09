"""Tests for DataValidator."""

import numpy as np
import pandas as pd
import pytest
from src.core.validation import DataValidator


@pytest.fixture
def validator():
    return DataValidator(target_column="ae_attendances", date_column="date")


@pytest.fixture
def valid_df():
    n = 20
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "date":          pd.date_range("2024-06-01", periods=n, freq="D"),
        "tmax_c":        rng.uniform(20, 35, n),
        "humidity_pct":  rng.uniform(40, 90, n),
        "ae_attendances": rng.integers(60, 250, n).astype(float),
    })


def test_validate_valid_dataframe(validator, valid_df):
    ok, errors, warnings = validator.validate_dataframe(valid_df)
    assert ok
    assert len(errors) == 0


def test_validate_missing_required_column(validator, valid_df):
    df = valid_df.drop(columns=["tmax_c"])
    ok, errors, _ = validator.validate_dataframe(df, required_columns=["date", "tmax_c"])
    assert not ok
    assert any("tmax_c" in str(e) for e in errors)


def test_validate_empty_dataframe(validator):
    ok, errors, _ = validator.validate_dataframe(pd.DataFrame())
    assert not ok
    assert any(e.get("type") == "empty" for e in errors)


def test_validate_target_no_nulls(validator, valid_df):
    ok, errors, _ = validator.validate_target_column(valid_df)
    assert ok
    assert len(errors) == 0


def test_validate_target_with_nulls(validator, valid_df):
    df = valid_df.copy()
    df.loc[0, "ae_attendances"] = None
    ok, errors, _ = validator.validate_target_column(df)
    assert not ok
    assert any("missing" in str(e).lower() for e in errors)


def test_validate_target_negative(validator, valid_df):
    df = valid_df.copy()
    df.loc[0, "ae_attendances"] = -5.0
    ok, errors, _ = validator.validate_target_column(df)
    assert not ok


def test_leakage_check_ordered_dates(validator, valid_df):
    result = validator.validate_leakage_prevention(valid_df)
    assert not result["leakage_detected"]
    assert any("Date ordering is correct" in c for c in result["checks_performed"])


def test_leakage_check_unordered_dates(validator, valid_df):
    df = valid_df.sample(frac=1, random_state=42)
    result = validator.validate_leakage_prevention(df)
    assert result["leakage_detected"]


def test_feature_order_valid(validator):
    expected = ["a", "b", "c"]
    result = validator.validate_feature_order(expected, ["a", "b", "c"])
    assert result["order_valid"]


def test_feature_order_mismatch(validator):
    result = validator.validate_feature_order(["a", "b", "c"], ["a", "c", "b"])
    assert not result["order_valid"]
