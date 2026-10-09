"""
pipeline.py — Orchestrate validation → feature engineering → preprocessing.
Strict leakage prevention: fit=True on training, fit=False on inference.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.config import settings
from src.core.features import FeatureEngineer
from src.core.preprocessing import DataPreprocessor
from src.core.validation import DataValidator

logger = logging.getLogger(__name__)


class HeatShieldPipeline:
    """End-to-end data preparation pipeline."""

    def __init__(
        self,
        data_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
    ):
        self.data_dir    = Path(data_dir    or settings.data_path)
        self.reports_dir = Path(reports_dir or settings.reports_path)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.feature_engineer = FeatureEngineer(
            date_column=settings.date_column,
            target_column=settings.target_column,
        )
        self.preprocessor = DataPreprocessor(
            missing_strategy=settings.missing_weather_strategy,
        )
        self.validator = DataValidator(
            target_column=settings.target_column,
            date_column=settings.date_column,
        )
        self.fitted: bool = False
        self.feature_columns: List[str] = []
        self.transformation_stats: Dict[str, Any] = {}

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_data(self, filepath: str, date_format: Optional[str] = None) -> pd.DataFrame:
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        df = pd.read_csv(file_path)
        if date_format:
            df[settings.date_column] = pd.to_datetime(df[settings.date_column], format=date_format)
        else:
            df[settings.date_column] = pd.to_datetime(df[settings.date_column])
        return df.sort_values(settings.date_column).reset_index(drop=True)

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_training_data(
        self, df: pd.DataFrame
    ) -> Tuple[bool, Dict[str, Any]]:
        is_valid, errors, warnings = self.validator.validate_dataframe(
            df, required_columns=[settings.date_column, settings.target_column]
        )
        t_valid, t_errors, t_warnings = self.validator.validate_target_column(df)
        errors.extend(t_errors)
        warnings.extend(t_warnings)

        leakage = self.validator.validate_leakage_prevention(df)
        if leakage["leakage_detected"]:
            is_valid = False

        return is_valid and t_valid, {
            "errors": errors, "warnings": warnings,
            "leakage_issues": leakage["issues"],
        }

    # ── Training preparation ──────────────────────────────────────────────────

    def prepare_training_data(
        self, df: pd.DataFrame, save_stats: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        is_valid, summary = self.validate_training_data(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {summary}")

        df = self.feature_engineer.engineer_all_features(df, fit=True)
        df, preprocess_stats = self.preprocessor.preprocess_pipeline(
            df, target_column=settings.target_column, fit=True
        )
        self.feature_columns = self.feature_engineer.feature_columns.copy()

        self.transformation_stats = {
            "feature_columns":      self.feature_columns,
            "preprocess_stats":     preprocess_stats,
            "feature_engineer_stats": self.feature_engineer.generate_feature_report(df),
            "validation_summary":   summary,
            "created_at":           datetime.now().isoformat(),
        }
        if save_stats:
            self.save_transformation_stats()

        self.fitted = True
        return df, self.transformation_stats

    # ── Inference preparation ─────────────────────────────────────────────────

    def prepare_inference_data(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        if not self.fitted:
            raise RuntimeError("Pipeline must be fitted before preparing inference data")

        df = self.feature_engineer.engineer_all_features(df, fit=False)
        df, _ = self.preprocessor.preprocess_pipeline(
            df, target_column=settings.target_column, fit=False
        )
        validation = self.feature_engineer.validate_features(df)
        if not validation["valid"]:
            raise ValueError(f"Missing features: {validation['missing_features']}")

        return df, validation

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_transformation_stats(self) -> Path:
        output_path = self.reports_dir / "transformation_stats.json"
        stats = {
            k: (str(v) if not isinstance(v, (dict, list, str, int, float, bool, type(None))) else v)
            for k, v in self.transformation_stats.items()
        }
        with open(output_path, "w") as f:
            json.dump(stats, f, indent=2)
        logger.info("Saved transformation stats to %s", output_path)
        return output_path

    def get_feature_columns(self) -> List[str]:
        return self.feature_engineer.feature_columns.copy()

    def get_transformation_stats(self) -> Dict[str, Any]:
        return self.transformation_stats.copy()

    def generate_dataset_schema(self) -> Dict[str, Any]:
        return {
            "created_at":     datetime.now().isoformat(),
            "schema_version": "1.0",
            "target": {
                "name":        settings.target_column,
                "description": "Daily heat-related ED visit count (UKHSA)",
                "type":        "integer",
                "units":       "count",
            },
            "input_columns":       self.feature_columns,
            "feature_statistics":  self.transformation_stats.get("preprocess_stats", {}),
        }
