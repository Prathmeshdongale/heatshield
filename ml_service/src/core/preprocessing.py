"""
preprocessing.py — Clean, normalise and encode data for ML training/inference.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocess data for ML models — fitting on training data only."""

    def __init__(self, missing_strategy: str = "mean"):
        self.missing_strategy = missing_strategy
        self.scaler: Optional[StandardScaler] = None
        self.min_max_scaler: Optional[MinMaxScaler] = None
        self.feature_columns: List[str] = []
        self.fitted: bool = False

    # ── Missing values ────────────────────────────────────────────────────────

    def handle_missing_values(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df = df.copy()
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        stats: Dict[str, Any] = {}
        for col in columns:
            if col not in df.columns:
                continue
            if self.missing_strategy == "mean":
                stats[col] = {"strategy": "mean", "value": df[col].mean()}
                df[col] = df[col].fillna(df[col].mean())
            elif self.missing_strategy == "median":
                stats[col] = {"strategy": "median", "value": df[col].median()}
                df[col] = df[col].fillna(df[col].median())
            elif self.missing_strategy == "forward_fill":
                df[col] = df[col].ffill().bfill()
                stats[col] = {"strategy": "forward_fill"}
            elif self.missing_strategy == "backward_fill":
                df[col] = df[col].bfill().ffill()
                stats[col] = {"strategy": "backward_fill"}
        return df, stats

    # ── Outlier removal ───────────────────────────────────────────────────────

    def remove_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        threshold: float = 3.0,
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        df = df.copy()
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outlier_info = []
        for col in columns:
            if col not in df.columns:
                continue
            z_scores = np.abs((df[col] - df[col].mean()) / (df[col].std() + 1e-9))
            mask = z_scores > threshold
            if mask.any():
                outlier_info.append({
                    "column": col,
                    "count": int(mask.sum()),
                    "percentage": float(mask.mean() * 100),
                })
                df = df[~mask]
        return df, outlier_info

    # ── Normalisation ─────────────────────────────────────────────────────────

    def normalize_features(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "standard",
        fit: bool = True,
    ) -> Tuple[pd.DataFrame, Any, List[str]]:
        df = df.copy()
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if fit:
            if method == "standard":
                self.scaler = StandardScaler()
                df[columns] = self.scaler.fit_transform(df[columns])
            else:
                self.min_max_scaler = MinMaxScaler()
                df[columns] = self.min_max_scaler.fit_transform(df[columns])
            self.feature_columns = list(columns)
        else:
            scaler = self.scaler or self.min_max_scaler
            if scaler is not None:
                df[columns] = scaler.transform(df[columns])

        active_scaler = self.scaler or self.min_max_scaler
        return df, active_scaler, self.feature_columns

    # ── Time features ─────────────────────────────────────────────────────────

    def create_time_features(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        df = df.copy()
        dates = pd.to_datetime(df[date_column])
        df["year"]        = dates.dt.year
        df["month"]       = dates.dt.month
        df["day"]         = dates.dt.day
        df["day_of_week"] = dates.dt.dayofweek
        df["day_of_year"] = dates.dt.dayofyear
        df["week_of_year"] = dates.dt.isocalendar().week
        df["is_weekend"]  = (dates.dt.dayofweek >= 5).astype(int)
        df["season"]      = df["month"].apply(self._get_season)
        return df

    def _get_season(self, month: int) -> str:
        if month in [12, 1, 2]:  return "winter"
        elif month in [3, 4, 5]: return "spring"
        elif month in [6, 7, 8]: return "summer"
        else:                     return "autumn"

    # ── Categorical encoding ──────────────────────────────────────────────────

    def encode_categorical(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        df = df.copy()
        if columns is None:
            columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
        category_mappings = {
            col: df[col].astype("category").cat.categories.tolist()
            for col in columns if col in df.columns
        }
        return pd.get_dummies(df, columns=columns, drop_first=True), category_mappings

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def preprocess_pipeline(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        fit: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Run the full preprocessing pipeline."""
        metadata: Dict[str, Any] = {}

        if "date" in df.columns:
            df = self.create_time_features(df, "date")
            metadata["time_features_created"] = True

        if fit:
            df, imputation_stats = self.handle_missing_values(df)
            metadata["imputation_stats"] = imputation_stats

        feature_columns = (
            [c for c in df.columns if c != target_column]
            if target_column and target_column in df.columns
            else list(df.columns)
        )
        # Only normalise numeric columns — skip datetime, object, category
        numeric_feature_cols = [
            c for c in feature_columns
            if pd.api.types.is_numeric_dtype(df[c])
        ]
        df, scaler, feat_cols = self.normalize_features(df, numeric_feature_cols, fit=fit)
        metadata.update({"feature_columns": feat_cols, "fitted": True})
        self.fitted = True
        return df, metadata
