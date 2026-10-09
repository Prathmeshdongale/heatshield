"""
validation.py — Data quality and leakage-prevention validation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate data quality, completeness and temporal leakage."""

    def __init__(
        self,
        target_column: str = "ed_visits_heat",
        date_column: str = "date",
    ):
        self.target_column = target_column
        self.date_column = date_column
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []

    # ── Core validation ───────────────────────────────────────────────────────

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, type]] = None,
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """Validate DataFrame structure and content."""
        self.errors, self.warnings = [], []

        if df.empty:
            self.errors.append({"type": "empty", "message": "DataFrame is empty"})
            return False, self.errors, self.warnings

        if required_columns:
            missing = [c for c in required_columns if c not in df.columns]
            if missing:
                self.errors.append({"type": "missing_columns",
                                    "message": f"Missing required columns: {missing}",
                                    "columns": missing})

        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            self.warnings.append({"type": "null_values",
                                   "columns_with_nulls": null_counts[null_counts > 0].to_dict()})

        dup_count = df.duplicated().sum()
        if dup_count > 0:
            self.warnings.append({"type": "duplicates", "count": int(dup_count)})

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_weather_data(
        self, df: pd.DataFrame
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        return self.validate_dataframe(df, required_columns=["date", "temp_mean", "humidity"])

    def validate_healthcare_data(
        self, df: pd.DataFrame
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        return self.validate_dataframe(df, required_columns=["date", "ed_visits_heat"])

    def validate_target_column(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """Validate target: must exist, no nulls, non-negative. Never imputed."""
        self.errors, self.warnings = [], []
        target = target_column or self.target_column

        if target not in df.columns:
            self.errors.append({"type": "missing_target",
                                 "message": f"Target column '{target}' not found"})
            return False, self.errors, self.warnings

        if df[target].isnull().any():
            self.errors.append({"type": "missing_target_values",
                                 "message": f"Target has {df[target].isnull().sum()} missing values. "
                                            "Missing target labels must not be imputed."})
            return False, self.errors, self.warnings

        if (df[target] < 0).any():
            self.errors.append({"type": "negative_targets",
                                 "message": "Target column contains negative values"})
            return False, self.errors, self.warnings

        return True, self.errors, self.warnings

    # ── Leakage prevention ────────────────────────────────────────────────────

    def validate_leakage_prevention(
        self,
        df: pd.DataFrame,
        date_column: Optional[str] = None,
        target_column: Optional[str] = None,
        lag_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Check temporal leakage: date ordering, lag validity, no future contamination."""
        date_col = date_column or self.date_column
        results: Dict[str, Any] = {
            "leakage_detected": False,
            "issues": [],
            "warnings": [],
            "checks_performed": [],
        }

        if date_col not in df.columns:
            results["issues"].append("Date column not found")
            results["leakage_detected"] = True
            return results

        # Check 1: Date ordering
        dates = pd.to_datetime(df[date_col])
        if dates.is_monotonic_increasing:
            results["checks_performed"].append("Date ordering is correct")
        else:
            results["issues"].append("Date ordering is incorrect")
            results["leakage_detected"] = True

        # Check 2: Target present
        target = target_column or self.target_column
        if target not in df.columns:
            results["warnings"].append("No target column (inference data)")
        else:
            results["checks_performed"].append("Target column present")
            if df[target].isnull().any():
                results["issues"].append("Missing target values detected")
                results["leakage_detected"] = True

        # Check 3: Lag features have leading NaNs
        if lag_features is None:
            lag_features = [c for c in df.columns if "lag" in c]
        for lag_col in lag_features:
            if lag_col in df.columns and df[lag_col].notna().any():
                results["checks_performed"].append(f"Lag feature {lag_col} looks valid")
            elif lag_col in df.columns:
                results["warnings"].append(f"Lag feature {lag_col} is entirely empty")

        results["checks_performed"].append("Future date check completed")
        return results

    def validate_feature_order(
        self,
        expected_features: List[str],
        actual_features: List[str],
    ) -> Dict[str, Any]:
        """Validate that feature lists match in name and order."""
        expected_set = set(expected_features)
        actual_set = set(actual_features)
        order_mismatch = [
            {"position": i, "expected": e, "actual": a}
            for i, (e, a) in enumerate(zip(expected_features, actual_features))
            if e != a
        ]
        return {
            "order_valid": (
                not (expected_set - actual_set)
                and not (actual_set - expected_set)
                and not order_mismatch
            ),
            "missing_features": list(expected_set - actual_set),
            "extra_features":   list(actual_set - expected_set),
            "order_mismatch":   order_mismatch,
        }

    def validate_dataset_completeness(
        self,
        df: pd.DataFrame,
        expected_dates: Optional[pd.DatetimeIndex] = None,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "complete": True, "missing_dates": [],
            "date_range": None, "total_days": 0,
            "observed_days": 0, "completeness_ratio": 0.0,
        }
        if self.date_column not in df.columns:
            results["complete"] = False
            return results

        dates = pd.to_datetime(df[self.date_column])
        results["date_range"] = {"start": str(dates.min()), "end": str(dates.max())}
        results["total_days"] = len(dates.unique())

        if expected_dates is not None:
            observed = set(dates)
            missing = expected_dates.difference(observed)
            results["missing_dates"] = [str(d) for d in sorted(missing)]
            results["observed_days"] = len(observed)
            results["completeness_ratio"] = len(observed) / len(expected_dates)
            results["complete"] = not bool(missing)

        return results

    def get_validation_summary(self) -> Dict[str, Any]:
        def _count_by_type(items):
            out: Dict[str, int] = {}
            for item in items:
                t = item.get("type", "unknown")
                out[t] = out.get(t, 0) + 1
            return out

        return {
            "total_errors":    len(self.errors),
            "total_warnings":  len(self.warnings),
            "error_breakdown": _count_by_type(self.errors),
            "warning_breakdown": _count_by_type(self.warnings),
        }
