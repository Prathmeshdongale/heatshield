"""
Data preprocessing module for ThermoCare AI.

This module provides functionality for cleaning and normalizing data.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Class for preprocessing data for ML models."""

    def __init__(self, missing_strategy: str = "mean"):
        """
        Initialize DataPreprocessor.

        Args:
            missing_strategy: Strategy for imputing missing values
                              ('mean', 'forward_fill', 'backward_fill')
        """
        self.missing_strategy = missing_strategy
        self.logger = logging.getLogger(__name__)
        self.scaler: Optional[StandardScaler] = None
        self.min_max_scaler: Optional[MinMaxScaler] = None
        self.feature_columns: List[str] = []
        self.fitted: bool = False

    def handle_missing_values(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing values in DataFrame using training-data-fitted strategy.

        Args:
            df: DataFrame with potential missing values
            columns: Columns to process (None for all numeric)

        Returns:
            Tuple of (cleaned DataFrame, imputation statistics)
        """
        df = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        imputation_stats = {}

        for col in columns:
            if col not in df.columns:
                continue

            if self.missing_strategy == "mean":
                imputation_stats[col] = {
                    "strategy": "mean",
                    "value": df[col].mean(),
                }
                df[col] = df[col].fillna(df[col].mean())
            elif self.missing_strategy == "median":
                imputation_stats[col] = {
                    "strategy": "median",
                    "value": df[col].median(),
                }
                df[col] = df[col].fillna(df[col].median())
            elif self.missing_strategy == "forward_fill":
                imputation_stats[col] = {
                    "strategy": "forward_fill",
                    "value": df[col].bfill().ffill().iloc[0] if df[col].isna().all() else None,
                }
                df[col] = df[col].ffill().bfill()
            elif self.missing_strategy == "backward_fill":
                imputation_stats[col] = {
                    "strategy": "backward_fill",
                    "value": df[col].bfill().ffill().iloc[0] if df[col].isna().all() else None,
                }
                df[col] = df[col].bfill().ffill()

        return df, imputation_stats

    def remove_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        threshold: float = 3.0,
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Remove outliers using z-score method.

        Args:
            df: DataFrame to process
            columns: Columns to check for outliers
            threshold: Z-score threshold for outlier detection

        Returns:
            Tuple of (cleaned DataFrame, outlier information)
        """
        df = df.copy()
        outlier_info = []

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outliers = z_scores > threshold

            if outliers.any():
                outlier_info.append({
                    "column": col,
                    "count": int(outliers.sum()),
                    "percentage": float(outliers.mean() * 100),
                })
                df = df[~outliers]

        return df, outlier_info

    def normalize_features(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "standard",
        fit: bool = True,
    ) -> Tuple[pd.DataFrame, object, List[str]]:
        """
        Normalize features in DataFrame.

        Args:
            df: DataFrame to normalize
            columns: Columns to normalize
            method: Normalization method ('standard', 'minmax')
            fit: Whether to fit the scaler (True for training, False for inference)

        Returns:
            Tuple of (normalized DataFrame, fitted scaler, feature_columns)
        """
        df = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if fit:
            if method == "standard":
                self.scaler = StandardScaler()
                df[columns] = self.scaler.fit_transform(df[columns])
                self.feature_columns = columns.copy()
                return df, self.scaler, self.feature_columns
            elif method == "minmax":
                self.min_max_scaler = MinMaxScaler()
                df[columns] = self.min_max_scaler.fit_transform(df[columns])
                self.feature_columns = columns.copy()
                return df, self.min_max_scaler, self.feature_columns
        else:
            # Use existing scaler for inference
            if self.scaler is not None:
                df[columns] = self.scaler.transform(df[columns])
                return df, self.scaler, self.feature_columns
            elif self.min_max_scaler is not None:
                df[columns] = self.min_max_scaler.transform(df[columns])
                return df, self.min_max_scaler, self.feature_columns

        return df, None, columns

    def encode_categorical(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """
        Encode categorical variables using one-hot encoding.

        Args:
            df: DataFrame to process
            columns: Categorical columns to encode

        Returns:
            Tuple of (encoded DataFrame, category mappings)
        """
        df = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

        category_mappings = {}
        for col in columns:
            if col in df.columns:
                category_mappings[col] = df[col].astype("category").cat.categories.tolist()

        return pd.get_dummies(df, columns=columns, drop_first=True), category_mappings

    def create_time_features(
        self,
        df: pd.DataFrame,
        date_column: str,
    ) -> pd.DataFrame:
        """
        Create time-based features from date column.

        Args:
            df: DataFrame with date column
            date_column: Name of date column

        Returns:
            DataFrame with additional time features
        """
        df = df.copy()

        dates = pd.to_datetime(df[date_column])
        df["year"] = dates.dt.year
        df["month"] = dates.dt.month
        df["day"] = dates.dt.day
        df["day_of_week"] = dates.dt.dayofweek
        df["day_of_year"] = dates.dt.dayofyear
        df["week_of_year"] = dates.dt.isocalendar().week
        df["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)

        # Season feature
        df["season"] = df["month"].apply(self._get_season)

        return df

    def _get_season(self, month: int) -> str:
        """
        Get season for a month.

        Args:
            month: Month number (1-12)

        Returns:
            Season string
        """
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    def preprocess_pipeline(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        fit: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Run full preprocessing pipeline.

        Args:
            df: Input DataFrame
            target_column: Target column name (will be excluded from scaling)
            fit: Whether to fit the scaler (True for training, False for inference)

        Returns:
            Tuple of (preprocessed DataFrame, transformation metadata)
        """
        self.logger.info("Running preprocessing pipeline")
        metadata = {}

        # Create time features
        if "date" in df.columns:
            df = self.create_time_features(df, "date")
            metadata["time_features_created"] = True

        # Handle missing values (only on training data)
        if fit:
            df, imputation_stats = self.handle_missing_values(df)
            metadata["imputation_stats"] = imputation_stats

        # Normalize features
        if target_column and target_column in df.columns:
            feature_columns = [c for c in df.columns if c != target_column]
            df, scaler, feature_cols = self.normalize_features(df, feature_columns, fit=fit)
            metadata["feature_columns"] = feature_cols
            metadata["scaler"] = scaler
        else:
            df, scaler, feature_cols = self.normalize_features(df, fit=fit)
            metadata["feature_columns"] = feature_cols
            metadata["scaler"] = scaler

        metadata["fitted"] = True
        self.fitted = True

        return df, metadata
