"""
train.py — Train, evaluate and persist ML models.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from src.config import settings
from src.core.features import FeatureEngineer
from src.core.preprocessing import DataPreprocessor

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train healthcare demand forecasting models."""

    MODELS = {
        "random_forest": RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        ),
        "ridge": Ridge(alpha=1.0),
    }

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = Path(models_dir or settings.models_path)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()

    # ── Data preparation ──────────────────────────────────────────────────────

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        target_column: str = "ae_attendances",
        feature_columns: Optional[list[str]] = None,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        # Normalise date column name
        if "timestamp" in df.columns and "date" not in df.columns:
            df = df.rename(columns={"timestamp": "date"})
        df = self.feature_engineer.engineer_all_features(df)
        df, _ = self.preprocessor.preprocess_pipeline(df)

        if feature_columns is None:
            # Keep only numeric columns — drop date/object/category
            feature_columns = [
                c for c in df.columns
                if c != target_column and pd.api.types.is_numeric_dtype(df[c])
            ]

        X = df[[c for c in feature_columns if c in df.columns]].fillna(0)
        y = df[target_column]
        return X, y

    # ── Training ──────────────────────────────────────────────────────────────

    def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_name: str = "random_forest",
        test_size: float = 0.2,
    ) -> Tuple[object, Dict]:
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Choose from {list(self.MODELS)}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        model = self.MODELS[model_name]
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        metrics = {
            "mae":  mean_absolute_error(y_test, y_pred),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2":   r2_score(y_test, y_pred),
        }
        cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
        metrics["cv_r2_mean"] = float(cv_scores.mean())
        metrics["cv_r2_std"]  = float(cv_scores.std())

        logger.info("Trained %s — R²=%.4f  MAE=%.2f", model_name, metrics["r2"], metrics["mae"])
        return model, metrics

    def train_all_models(
        self, X: pd.DataFrame, y: pd.Series
    ) -> Dict[str, Tuple[object, Dict]]:
        results = {}
        for name in self.MODELS:
            try:
                model, metrics = self.train_model(X, y, model_name=name)
                results[name] = (model, metrics)
            except Exception as exc:
                logger.error("Failed to train %s: %s", name, exc)
        return results

    def select_best_model(
        self,
        results: Dict[str, Tuple[object, Dict]],
        metric: str = "r2",
    ) -> Tuple[str, object, Dict]:
        best_name, best_model, best_metrics = None, None, None
        best_value = -np.inf
        for name, (model, metrics) in results.items():
            value = metrics.get(metric, -np.inf)
            if value > best_value:
                best_value, best_name, best_model, best_metrics = value, name, model, metrics
        return best_name, best_model, best_metrics  # type: ignore[return-value]

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_model(self, model: object, model_name: str, version: str = "v1") -> Path:
        output_path = self.models_dir / f"{model_name}_{version}.joblib"
        dump(model, output_path)
        logger.info("Saved model to %s", output_path)
        return output_path

    def save_metrics(self, metrics: Dict, model_name: str, version: str = "v1") -> Path:
        metrics_path = self.models_dir / f"{model_name}_{version}_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        return metrics_path

    def load_model(self, model_name: str, version: str = "v1") -> object:
        from joblib import load
        model_path = self.models_dir / f"{model_name}_{version}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        return load(model_path)

    def get_model_metrics(self, model_name: str, version: str = "v1") -> Dict:
        metrics_path = self.models_dir / f"{model_name}_{version}_metrics.json"
        if metrics_path.exists():
            with open(metrics_path) as f:
                return json.load(f)
        return {}
