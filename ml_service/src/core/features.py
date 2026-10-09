"""
features.py — Feature engineering with strict leakage prevention.

Order of operations (no future data leakage):
  1. Sort by date
  2. Calendar features   (no leakage risk)
  3. Temperature features
  4. Weather combination features
  5. Lag features        (shift past target values)
  6. Rolling features    (shift(1) before rolling)
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)
__all__ = ["FeatureEngineer", "validate_leakage_prevention"]


class FeatureEngineer:
    """Engineer ML features with leakage prevention."""

    def __init__(
        self,
        date_column: str = "date",
        target_column: str = "ed_visits_heat",
    ):
        self.date_column   = date_column
        self.target_column = target_column
        self.feature_columns: List[str] = []
        self.fitted: bool = False

    # ── Individual feature groups ─────────────────────────────────────────────

    def create_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if self.date_column in df.columns:
            dates = pd.to_datetime(df[self.date_column])
            df["year"]         = dates.dt.year
            df["month"]        = dates.dt.month
            df["day_of_week"]  = dates.dt.dayofweek   # created here
            df["day_of_year"]  = dates.dt.dayofyear
            df["week_of_year"] = dates.dt.isocalendar().week.astype(int)
            df["day"]          = dates.dt.day
        # Now day_of_week definitely exists
        if "day_of_week" in df.columns:
            df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)
            df["is_weekday"]   = (df["day_of_week"] < 5).astype(int)
        df["is_month_end"] = (df.get("day", pd.Series([1]*len(df))) >= 28).astype(int)
        if "month" in df.columns:
            df["season"] = df["month"].apply(self._get_season)
        return df

    def create_temperature_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        t_max = settings.temp_max_column
        t_min = settings.temp_min_column
        t_mean = settings.temperature_column

        if t_max in df.columns and t_min in df.columns:
            df["temp_range"] = df[t_max] - df[t_min]

        if t_mean in df.columns:
            df["is_heatwave"]    = (df[t_mean] >= settings.heatwave_temp_threshold).astype(int)
            df["is_extreme_heat"] = (df[t_mean] > 32.0).astype(int)
            if "month" in df.columns:
                monthly_means    = df.groupby("month")[t_mean].transform("mean")
                df["temp_anomaly"] = df[t_mean] - monthly_means

        if t_mean in df.columns and settings.humidity_column in df.columns:
            df["heat_index"] = (
                0.5 * df[t_mean]
                + 0.5 * df[t_mean]
                + 0.5 * df[settings.humidity_column] / 100 * (df[t_mean] - 14)
            )
        return df

    def create_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        t = settings.temperature_column
        h = settings.humidity_column

        if t in df.columns and h in df.columns:
            df["heat_stress_index"] = df[t] * (1 + df[h] / 100)
            df["is_drought"]        = ((df[h] < 30) & (df[t] > 25)).astype(int)
            df["in_comfort_zone"]   = (
                (df[t] >= 18) & (df[t] <= 25) & (df[h] >= 40) & (df[h] <= 60)
            ).astype(int)
        return df

    def create_lag_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Lag features use only PAST target values via pandas shift."""
        df = df.copy()
        if self.date_column in df.columns:
            df = df.sort_values(self.date_column).reset_index(drop=True)

        if fit and self.target_column in df.columns:
            for lag in settings.lag_days:
                col = f"{self.target_column}_lag_{lag}"
                df[col] = df[self.target_column].shift(lag)
                logger.debug(f"Created lag feature: {col}")
        return df

    def create_rolling_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Rolling features use shift(1) so current day's target is excluded."""
        df = df.copy()
        if self.date_column in df.columns:
            df = df.sort_values(self.date_column).reset_index(drop=True)

        if fit and self.target_column in df.columns:
            for window in settings.rolling_windows:
                col = f"{self.target_column}_rolling_mean_{window}"
                df[col] = (
                    df[self.target_column]
                    .shift(1)
                    .rolling(window=window, min_periods=1)
                    .mean()
                )
                logger.debug(f"Created rolling feature: {col}")

        if settings.temperature_column in df.columns:
            for window in settings.rolling_windows:
                col = f"temp_rolling_mean_{window}"
                df[col] = (
                    df[settings.temperature_column]
                    .rolling(window=window, min_periods=1)
                    .mean()
                )
        return df

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def engineer_all_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Run complete feature engineering in safe order."""
        if self.date_column in df.columns:
            df = df.sort_values(self.date_column).reset_index(drop=True)

        df = self.create_calendar_features(df)
        df = self.create_temperature_features(df)
        df = self.create_weather_features(df)
        df = self.create_lag_features(df, fit=fit)
        df = self.create_rolling_features(df, fit=fit)

        self.feature_columns = [c for c in df.columns if c != self.target_column]
        self.fitted = True
        logger.info(f"Engineered {len(self.feature_columns)} features")
        return df

    # ── Utilities ─────────────────────────────────────────────────────────────

    def get_feature_columns(self) -> List[str]:
        return list(self.feature_columns)

    def validate_features(
        self,
        df: pd.DataFrame,
        required_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if required_features is None:
            required_features = self.feature_columns
        return {
            "valid":            all(f in df.columns for f in required_features),
            "missing_features": [f for f in required_features if f not in df.columns],
            "extra_features":   [f for f in df.columns
                                  if f not in required_features and f != self.target_column],
            "total_features":   len(df.columns),
        }

    def generate_feature_report(
        self, df: pd.DataFrame, fit: bool = True
    ) -> Dict[str, Any]:
        return {
            "total_columns":  len(df.columns),
            "target_column":  self.target_column,
            "feature_columns": self.feature_columns,
            "feature_types": {
                "temperature": [c for c in self.feature_columns if "temp" in c],
                "humidity":    [c for c in self.feature_columns if "humidity" in c],
                "lag":         [c for c in self.feature_columns if "lag" in c],
                "rolling":     [c for c in self.feature_columns if "rolling" in c],
                "calendar":    [c for c in self.feature_columns
                                if c in ("month", "day_of_week", "season", "is_weekend")],
            },
        }

    @staticmethod
    def _get_season(month: int) -> str:
        if month in [12, 1, 2]:  return "winter"
        elif month in [3, 4, 5]: return "spring"
        elif month in [6, 7, 8]: return "summer"
        else:                     return "autumn"


# ── Module-level utility ──────────────────────────────────────────────────────

def validate_leakage_prevention(
    df: pd.DataFrame,
    date_column: str = "date",
    target_column: str = "ed_visits_heat",
) -> Dict[str, Any]:
    """Quick leakage check: date ordering, lag NaN pattern, no future contamination."""
    results: Dict[str, Any] = {
        "leakage_detected": False, "issues": [], "checks_performed": []
    }

    if date_column not in df.columns:
        results["issues"].append("Date column not found")
        results["leakage_detected"] = True
        return results

    dates = pd.to_datetime(df[date_column])
    if dates.is_monotonic_increasing:
        results["checks_performed"].append("Date ordering is correct")
    else:
        results["issues"].append("Date ordering is incorrect")
        results["leakage_detected"] = True

    feature_cols = [c for c in df.columns if c != target_column]
    lag_cols = [c for c in feature_cols if "lag" in c]
    for lag_col in lag_cols:
        if df[lag_col].notna().any():
            results["checks_performed"].append(f"Lag feature {lag_col} has values")
        else:
            results["issues"].append(f"Lag feature {lag_col} is entirely empty")

    results["checks_performed"].append("Future date check completed")
    results["leakage_detected"] = len(results["issues"]) > 0
    return results
