"""
Data pipeline for HeatShield.

This module orchestrates the feature engineering and data preparation pipeline
with strict leakage prevention and data quality validation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd

from app.config import settings
from app.ml.features import FeatureEngineer
from app.ml.preprocessing import DataPreprocessor
from app.ml.validation import DataValidator

logger = logging.getLogger(__name__)


class HeatShieldPipeline:
    """Pipeline for data preparation and feature engineering with leakage prevention."""

    def __init__(
        self,
        data_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
    ):
        """
        Initialize HeatShieldPipeline.

        Args:
            data_dir: Path to data directory
            reports_dir: Path to reports directory
        """
        self.data_dir = Path(data_dir or settings.data_path)
        self.reports_dir = Path(reports_dir or settings.reports_path)

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
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

    def load_data(
        self,
        filepath: str,
        date_format: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load data from file.

        Args:
            filepath: Path to data file
            date_format: Optional date format string

        Returns:
            Loaded DataFrame
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        logger.info(f"Loading data from {file_path}")

        df = pd.read_csv(file_path)

        # Parse date column if specified
        if date_format:
            df[settings.date_column] = pd.to_datetime(
                df[settings.date_column],
                format=date_format,
            )
        else:
            df[settings.date_column] = pd.to_datetime(df[settings.date_column])

        return df.sort_values(settings.date_column).reset_index(drop=True)

    def validate_training_data(
        self,
        df: pd.DataFrame,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate training data meets requirements.

        Args:
            df: Training DataFrame

        Returns:
            Tuple of (is_valid, validation_summary)
        """
        logger.info("Validating training data")

        # Validate required columns
        required_columns = [settings.date_column, settings.target_column]
        is_valid, errors, warnings = self.validator.validate_dataframe(
            df, required_columns=required_columns
        )

        # Validate target column (no missing values)
        target_valid, target_errors, target_warnings = self.validator.validate_target_column(df)

        is_valid = is_valid and target_valid
        errors.extend(target_errors)
        warnings.extend(target_warnings)

        # Validate leakage prevention
        leakage_results = self.validator.validate_leakage_prevention(df)
        is_valid = is_valid and not leakage_results["leakage_detected"]
        if leakage_results["issues"]:
            errors.extend([{"type": f"leakage_{i}", "message": msg} for i, msg in enumerate(leakage_results["issues"])])

        return is_valid, {
            "errors": errors,
            "warnings": warnings,
            "leakage_issues": leakage_results["issues"],
        }

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        save_stats: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Prepare training data with feature engineering.

        This method:
        1. Validates data quality
        2. Engineers features with leakage prevention
        3. Preprocesses features
        4. Records transformation statistics

        Args:
            df: Input DataFrame
            save_stats: Whether to save transformation statistics

        Returns:
            Tuple of (processed DataFrame, transformation statistics)
        """
        logger.info("Preparing training data")

        # Step 1: Validate
        is_valid, validation_summary = self.validate_training_data(df)
        if not is_valid:
            logger.error("Data validation failed")
            raise ValueError(f"Data validation failed: {validation_summary}")

        # Step 2: Engineer features (fit=True for training)
        df_processed = self.feature_engineer.engineer_all_features(df, fit=True)
        logger.info(f"Engineered {len(self.feature_engineer.feature_columns)} features")

        # Step 3: Preprocess features
        df_processed, preprocess_stats = self.preprocessor.preprocess_pipeline(
            df_processed,
            target_column=settings.target_column,
            fit=True,
        )

        # Step 4: Store transformation statistics
        self.transformation_stats = {
            "feature_columns": self.feature_engineer.feature_columns.copy(),
            "preprocess_stats": preprocess_stats,
            "feature_engineer_stats": self.feature_engineer.generate_feature_report(df_processed, fit=True),
            "validation_summary": validation_summary,
            "created_at": datetime.now().isoformat(),
        }

        if save_stats:
            self.save_transformation_stats()

        self.fitted = True

        return df_processed, self.transformation_stats

    def prepare_inference_data(
        self,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Prepare inference data using fitted transformation statistics.

        This method:
        1. Engineers features (fit=False to avoid using target)
        2. Preprocesses using fitted scaler
        3. Validates feature presence

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metadata)
        """
        if not self.fitted:
            raise RuntimeError("Pipeline must be fitted before preparing inference data")

        logger.info("Preparing inference data")

        # Step 1: Engineer features (fit=False for inference)
        df_processed = self.feature_engineer.engineer_all_features(df, fit=False)

        # Step 2: Preprocess using fitted scaler
        df_processed, _ = self.preprocessor.preprocess_pipeline(
            df_processed,
            target_column=settings.target_column,
            fit=False,
        )

        # Step 3: Validate features
        validation = self.feature_engineer.validate_features(df_processed)
        if not validation["valid"]:
            logger.error(f"Feature validation failed: {validation['missing_features']}")
            raise ValueError(f"Missing features: {validation['missing_features']}")

        return df_processed, validation

    def save_transformation_stats(self) -> Path:
        """
        Save transformation statistics to disk.

        Returns:
            Path to saved statistics file
        """
        output_path = self.reports_dir / "transformation_stats.json"

        # Convert Path objects to strings for JSON serialization
        stats = self.transformation_stats.copy()
        if "preprocess_stats" in stats and "imputation_stats" in stats["preprocess_stats"]:
            imputation = stats["preprocess_stats"]["imputation_stats"]
            for col, val in imputation.items():
                if isinstance(val, dict) and "value" in val:
                    if isinstance(val["value"], (Path, datetime)):
                        imputation[col]["value"] = str(val["value"])

        with open(output_path, "w") as f:
            json.dump(stats, f, indent=2)

        logger.info(f"Saved transformation statistics to {output_path}")
        return output_path

    def get_feature_columns(self) -> List[str]:
        """Get the list of feature columns used by the fitted model."""
        return self.feature_engineer.feature_columns.copy()

    def get_transformation_stats(self) -> Dict[str, Any]:
        """Get the transformation statistics."""
        return self.transformation_stats.copy()

    def generate_dataset_schema(self) -> Dict[str, Any]:
        """
        Generate a complete dataset schema for documentation.

        Returns:
            Dictionary containing the complete dataset schema
        """
        schema = {
            "created_at": datetime.now().isoformat(),
            "schema_version": "1.0",
            "target": {
                "name": settings.target_column,
                "description": "Daily count of heat-related emergency department visits from UKHSA",
                "type": "integer",
                "units": "count",
            },
            "input_columns": self.feature_engineer.feature_columns,
            "feature_statistics": {},
        }

        # Add feature statistics if we have them
        if self.transformation_stats:
            schema["feature_statistics"] = self.transformation_stats.get(
                "preprocess_stats", {}
            )

        return schema


def create_training_dataset(
    raw_data_path: str,
    output_path: Optional[str] = None,
) -> Tuple[pd.DataFrame, HeatShieldPipeline]:
    """
    Create a training dataset from raw data.

    This is a convenience function that:
    1. Loads raw data
    2. Validates the data
    3. Engineers features
    4. Preprocesses features
    5. Saves the processed data

    Args:
        raw_data_path: Path to raw data file
        output_path: Optional path to save processed data

    Returns:
        Tuple of (processed DataFrame, fitted pipeline)
    """
    logger.info("Creating training dataset")

    # Initialize pipeline
    pipeline = HeatShieldPipeline()

    # Load data
    df = pipeline.load_data(raw_data_path)

    # Prepare data
    df_processed, stats = pipeline.prepare_training_data(df)

    # Save if output path specified
    if output_path:
        df_processed.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")

    return df_processed, pipeline


def validate_feature_order(
    expected_features: List[str],
    actual_features: List[str],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that actual features match expected features in order.

    Args:
        expected_features: Expected feature column names
        actual_features: Actual feature column names

    Returns:
        Tuple of (is_valid, validation_summary)
    """
    validator = DataValidator()
    results = validator.validate_feature_order(expected_features, actual_features)

    return results["order_valid"], results
