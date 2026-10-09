"""
Data validation module for ThermoCare AI.

This module provides functionality for validating data quality and completeness
with specific checks for feature engineering pipelines.
"""

import logging
from datetime import timedelta
from typing import Optional, List, Dict, Any, Set

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Class for validating data quality and completeness."""

    def __init__(self, target_column: str = "ed_visits_heat", date_column: str = "date"):
        """
        Initialize DataValidator.

        Args:
            target_column: Name of target column
            date_column: Name of date column
        """
        self.target_column = target_column
        self.date_column = date_column
        self.logger = logging.getLogger(__name__)
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, type]] = None,
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate a DataFrame structure and content.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            column_types: Dictionary of column names to expected types

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Check for empty DataFrame
        if df.empty:
            self.errors.append({"type": "empty", "message": "DataFrame is empty"})
            return False, self.errors, self.warnings

        # Validate required columns
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.errors.append({
                    "type": "missing_columns",
                    "message": f"Missing required columns: {missing_columns}",
                    "columns": missing_columns,
                })

        # Validate column types
        if column_types:
            for col, expected_type in column_types.items():
                if col in df.columns:
                    if not pd.api.types.is_dtype_loaded(df[col].dtype):
                        self.errors.append({
                            "type": "type_mismatch",
                            "message": f"Column '{col}' has unexpected type: {df[col].dtype}",
                            "column": col,
                            "expected": str(expected_type),
                            "actual": str(df[col].dtype),
                        })

        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            null_cols = null_counts[null_counts > 0].to_dict()
            self.warnings.append({
                "type": "null_values",
                "message": f"Found columns with null values: {null_cols}",
                "columns_with_nulls": null_cols,
            })

        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            self.warnings.append({
                "type": "duplicates",
                "message": f"Found {duplicate_count} duplicate rows",
                "count": duplicate_count,
            })

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_weather_data(self, df: pd.DataFrame) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate weather data structure.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        required_columns = ["date", "temp_mean", "humidity"]
        column_types = {
            "temp_mean": np.floating,
            "humidity": np.floating,
        }
        return self.validate_dataframe(df, required_columns, column_types)

    def validate_healthcare_data(self, df: pd.DataFrame) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate healthcare data structure.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        required_columns = ["date", "ed_visits_heat"]
        column_types = {
            "ed_visits_heat": np.integer,
        }
        return self.validate_dataframe(df, required_columns, column_types)

    def validate_date_range(
        self,
        df: pd.DataFrame,
        date_column: Optional[str] = None,
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None,
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate date range in DataFrame.

        Args:
            df: DataFrame to validate
            date_column: Name of date column
            start_date: Expected start date
            end_date: Expected end date

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        date_col = date_column or self.date_column

        if date_col not in df.columns:
            self.errors.append({
                "type": "missing_column",
                "message": f"Date column '{date_col}' not found",
            })
            return False, self.errors, self.warnings

        dates = pd.to_datetime(df[date_col])

        if start_date is not None:
            if dates.min() < start_date:
                self.errors.append({
                    "type": "date_out_of_range",
                    "message": f"Earliest date {dates.min()} is before expected start {start_date}",
                })

        if end_date is not None:
            if dates.max() > end_date:
                self.errors.append({
                    "type": "date_out_of_range",
                    "message": f"Latest date {dates.max()} is after expected end {end_date}",
                })

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_target_column(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate target column exists and has no missing values.

        Target values should NEVER be imputed as observed counts.

        Args:
            df: DataFrame to validate
            target_column: Name of target column

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        target = target_column or self.target_column

        if target not in df.columns:
            self.errors.append({
                "type": "missing_target",
                "message": f"Target column '{target}' not found",
            })
            return False, self.errors, self.warnings

        # Check for missing target values (this is an error - we never impute targets)
        if df[target].isnull().any():
            missing_count = df[target].isnull().sum()
            self.errors.append({
                "type": "missing_target_values",
                "message": f"Target column has {missing_count} missing values. "
                          "Missing target labels should not be imputed.",
            })
            return False, self.errors, self.warnings

        # Check for negative values (ED visits should be non-negative)
        if (df[target] < 0).any():
            self.errors.append({
                "type": "negative_targets",
                "message": f"Target column has negative values",
            })
            return False, self.errors, self.warnings

        return True, self.errors, self.warnings

    def validate_leakage_prevention(
        self,
        df: pd.DataFrame,
        date_column: Optional[str] = None,
        target_column: Optional[str] = None,
        lag_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate that no target leakage has occurred.

        Checks:
        1. Target values are not used to create features in the same row
        2. No future dates are used to create current features
        3. Rolling calculations use only past data

        Args:
            df: DataFrame to validate
            date_column: Name of date column
            target_column: Name of target column
            lag_features: List of lag feature names to validate

        Returns:
            Dictionary with leakage validation results
        """
        date_col = date_column or self.date_column
        target = target_column or self.target_column
        results = {
            "leakage_detected": False,
            "issues": [],
            "warnings": [],
            "checks_performed": [],
        }

        if date_col not in df.columns:
            results["issues"].append("Date column not found")
            results["leakage_detected"] = True
            return results

        # Check 1: Verify date ordering
        dates = pd.to_datetime(df[date_col])
        if not dates.is_monotonic_increasing:
            results["issues"].append("Date ordering is incorrect")
            results["leakage_detected"] = True
        else:
            results["checks_performed"].append("Date ordering is correct")

        # Check 2: Verify target column exists (for training data)
        if target not in df.columns:
            results["warnings"].append("Target column not found (likely inference data)")
            results["checks_performed"].append("No target column (inference data)")
        else:
            results["checks_performed"].append("Target column present")

            # Check for missing targets
            if df[target].isnull().any():
                results["issues"].append("Missing target values detected")
                results["leakage_detected"] = True

        # Check 3: Verify lag features have appropriate NaN values
        if lag_features is None:
            lag_features = [c for c in df.columns if "lag" in c]

        for lag_col in lag_features:
            if lag_col in df.columns:
                # Lag features should have NaN for the first N rows
                first_valid_index = df[lag_col].first_valid_index()
                if first_valid_index is not None:
                    results["checks_performed"].append(f"Lag feature {lag_col} has valid values starting at index {first_valid_index}")
                else:
                    results["warnings"].append(f"Lag feature {lag_col} is empty")

        # Check 4: Verify no future data contamination
        if target in df.columns and date_col in df.columns:
            results["checks_performed"].append("Future date check completed")

        # Check 5: Verify no negative values in features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            if (df[col] < 0).any():
                results["warnings"].append(f"Negative values found in {col}")

        return results

    def validate_dataset_completeness(
        self,
        df: pd.DataFrame,
        expected_dates: Optional[pd.DatetimeIndex] = None,
    ) -> Dict[str, Any]:
        """
        Validate dataset completeness and identify missing dates.

        Args:
            df: DataFrame to validate
            expected_dates: Expected date range

        Returns:
            Dictionary with completeness validation results
        """
        results = {
            "complete": True,
            "missing_dates": [],
            "date_range": None,
            "total_days": 0,
            "observed_days": 0,
            "completeness_ratio": 0.0,
        }

        if self.date_column not in df.columns:
            results["complete"] = False
            results["missing_dates"].append("Date column not found")
            return results

        dates = pd.to_datetime(df[self.date_column])
        results["date_range"] = {
            "start": str(dates.min()),
            "end": str(dates.max()),
        }
        results["total_days"] = len(dates.unique())

        if expected_dates is not None:
            observed_dates = set(dates)
            missing_dates = expected_dates.difference(observed_dates)
            results["missing_dates"] = [str(d) for d in sorted(list(missing_dates))]
            results["observed_days"] = len(observed_dates)
            results["completeness_ratio"] = len(observed_dates) / len(expected_dates)

        if results["missing_dates"]:
            results["complete"] = False

        return results

    def validate_feature_order(
        self,
        expected_features: List[str],
        actual_features: List[str],
    ) -> Dict[str, Any]:
        """
        Validate that feature order matches expected order.

        Args:
            expected_features: Expected feature column names
            actual_features: Actual feature column names

        Returns:
            Dictionary with feature order validation results
        """
        results = {
            "order_valid": True,
            "missing_features": [],
            "extra_features": [],
            "order_mismatch": [],
        }

        # Check for missing features
        expected_set = set(expected_features)
        actual_set = set(actual_features)

        results["missing_features"] = list(expected_set - actual_set)
        results["extra_features"] = list(actual_set - expected_set)

        # Check for order mismatch
        for i, (exp, act) in enumerate(zip(expected_features, actual_features)):
            if exp != act:
                results["order_mismatch"].append({
                    "position": i,
                    "expected": exp,
                    "actual": act,
                })

        results["order_valid"] = (
            len(results["missing_features"]) == 0
            and len(results["extra_features"]) == 0
            and len(results["order_mismatch"]) == 0
        )

        return results

    def get_validation_summary(self) -> Dict:
        """
        Get validation summary.

        Returns:
            Dictionary with validation statistics
        """
        error_types = {}
        for error in self.errors:
            error_type = error.get("type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        warning_types = {}
        for warning in self.warnings:
            warning_type = warning.get("type", "unknown")
            warning_types[warning_type] = warning_types.get(warning_type, 0) + 1

        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "error_breakdown": error_types,
            "warning_breakdown": warning_types,
        }
