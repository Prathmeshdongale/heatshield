"""
Model training module for ThermoCare AI.

This module provides functionality for training ML models.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.config import settings
from app.ml.preprocessing import DataPreprocessor
from app.ml.features import FeatureEngineer

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Class for training healthcare demand forecasting models."""

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize ModelTrainer.

        Args:
            models_dir: Path to models directory
        """
        self.models_dir = Path(models_dir or settings.models_path)
        self.logger = logging.getLogger(__name__)

        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Initialize preprocessing and feature engineering
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()

        # Model configuration
        self.models = {
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                random_state=42,
            ),
            "ridge": Ridge(alpha=1.0),
        }

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        target_column: str = "a&e_visits",
        feature_columns: Optional[list[str]] = None,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for training.

        Args:
            df: Input DataFrame
            target_column: Name of target column
            feature_columns: List of feature columns (None for automatic)

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        self.logger.info("Preparing training data")

        # Create features
        df = self.feature_engineer.engineer_all_features(df)

        # Preprocess
        df = self.preprocessor.preprocess_pipeline(df)

        # Select features
        if feature_columns is None:
            feature_columns = [
                col for col in df.columns
                if col != target_column
                and not col.startswith("is_weekend")  # Exclude basic time features
            ]

        X = df[feature_columns].fillna(0)
        y = df[target_column]

        return X, y

    def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_name: str = "random_forest",
        test_size: float = 0.2,
    ) -> tuple[object, dict]:
        """
        Train a model.

        Args:
            X: Features DataFrame
            y: Target Series
            model_name: Name of model to train
            test_size: Test set size

        Returns:
            Tuple of (trained model, metrics dictionary)
        """
        self.logger.info(f"Training {model_name} model")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42,
        )

        # Get model
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Unknown model: {model_name}")

        # Train model
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred),
        }

        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
        metrics["cv_r2_mean"] = cv_scores.mean()
        metrics["cv_r2_std"] = cv_scores.std()

        return model, metrics

    def train_all_models(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> dict[str, tuple[object, dict]]:
        """
        Train all configured models.

        Args:
            X: Features DataFrame
            y: Target Series

        Returns:
            Dictionary mapping model names to (model, metrics) tuples
        """
        results = {}
        for model_name in self.models.keys():
            try:
                model, metrics = self.train_model(X, y, model_name)
                results[model_name] = (model, metrics)
                self.logger.info(f"Trained {model_name}: R² = {metrics['r2']:.4f}")
            except Exception as e:
                self.logger.error(f"Failed to train {model_name}: {e}")

        return results

    def select_best_model(
        self,
        results: dict[str, tuple[object, dict]],
        metric: str = "r2",
    ) -> tuple[str, object, dict]:
        """
        Select the best model based on metric.

        Args:
            results: Training results dictionary
            metric: Metric to optimize

        Returns:
            Tuple of (model name, model, metrics)
        """
        best_model = None
        best_metrics = None
        best_name = None
        best_value = -np.inf

        for name, (model, metrics) in results.items():
            value = metrics.get(metric, -np.inf)
            if value > best_value:
                best_value = value
                best_model = model
                best_metrics = metrics
                best_name = name

        return best_name, best_model, best_metrics

    def save_model(
        self,
        model: object,
        model_name: str,
        version: str = "v1",
    ) -> Path:
        """
        Save trained model to disk.

        Args:
            model: Trained model
            model_name: Name for the model
            version: Model version

        Returns:
            Path to saved model
        """
        output_path = self.models_dir / f"{model_name}_{version}.joblib"
        joblib.dump(model, output_path)
        self.logger.info(f"Saved model to {output_path}")
        return output_path

    def load_model(
        self,
        model_name: str,
        version: str = "v1",
    ) -> object:
        """
        Load a trained model from disk.

        Args:
            model_name: Name of model
            version: Model version

        Returns:
            Loaded model
        """
        model_path = self.models_dir / f"{model_name}_{version}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.logger.info(f"Loading model from {model_path}")
        return joblib.load(model_path)

    def get_model_metrics(
        self,
        model_name: str,
        version: str = "v1",
    ) -> dict:
        """
        Get metrics for a saved model.

        Args:
            model_name: Name of model
            version: Model version

        Returns:
            Model metrics dictionary
        """
        metrics_path = self.models_dir / f"{model_name}_{version}_metrics.json"
        if metrics_path.exists():
            import json
            with open(metrics_path) as f:
                return json.load(f)
        return {}
