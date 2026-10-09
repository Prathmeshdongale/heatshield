"""
Model evaluation module for ThermoCare AI.

This module provides functionality for evaluating ML model performance.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error, median_absolute_error
)
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Class for evaluating healthcare demand forecasting models."""

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize ModelEvaluator.

        Args:
            models_dir: Path to models directory
        """
        self.models_dir = Path(models_dir or "")
        self.logger = logging.getLogger(__name__)

    def calculate_regression_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> dict[str, float]:
        """
        Calculate standard regression metrics.

        Args:
            y_true: True target values
            y_pred: Predicted values

        Returns:
            Dictionary of metric names and values
        """
        metrics = {
            "mae": mean_absolute_error(y_true, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            "r2": r2_score(y_true, y_pred),
            "mape": mean_absolute_percentage_error(y_true, y_pred) if np.any(y_true != 0) else 0,
            "medae": median_absolute_error(y_true, y_pred),
        }

        # Normalized metrics
        if np.mean(y_true) != 0:
            metrics["nmse"] = metrics["rmse"] / np.mean(y_true)
            metrics["mae_ratio"] = metrics["mae"] / np.mean(y_true)

        return metrics

    def calculate_error_distribution(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> dict[str, float]:
        """
        Calculate error distribution statistics.

        Args:
            y_true: True target values
            y_pred: Predicted values

        Returns:
            Dictionary of error distribution statistics
        """
        errors = y_true - y_pred

        return {
            "mean_error": np.mean(errors),
            "std_error": np.std(errors),
            "min_error": np.min(errors),
            "max_error": np.max(errors),
            "median_error": np.median(errors),
            "p95_error": np.percentile(errors, 95),
            "p5_error": np.percentile(errors, 5),
        }

    def calculate_skill_scores(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_baseline: Optional[np.ndarray] = None,
    ) -> dict[str, float]:
        """
        Calculate skill scores comparing to baseline.

        Args:
            y_true: True target values
            y_pred: Predicted values
            y_baseline: Baseline predictions (e.g., naive forecast)

        Returns:
            Dictionary of skill scores
        """
        metrics = self.calculate_regression_metrics(y_true, y_pred)

        if y_baseline is not None:
            baseline_metrics = self.calculate_regression_metrics(y_true, y_baseline)

            # Improvement scores (higher is better)
            metrics["r2_improvement"] = metrics["r2"] - baseline_metrics["r2"]
            metrics["mae_improvement"] = baseline_metrics["mae"] - metrics["mae"]
            metrics["rmse_improvement"] = baseline_metrics["rmse"] - metrics["rmse"]

            # Skill score (0 = baseline, 1 = perfect)
            if baseline_metrics["r2"] != 1:
                metrics["skill_score"] = (metrics["r2"] - baseline_metrics["r2"]) / (1 - baseline_metrics["r2"])

        return metrics

    def cross_validate_model(
        self,
        model,
        X: pd.DataFrame,
        y: pd.Series,
        cv: int = 5,
        scoring: str = "r2",
    ) -> dict[str, float]:
        """
        Perform cross-validation.

        Args:
            model: Trained model
            X: Features DataFrame
            y: Target Series
            cv: Number of cross-validation folds
            scoring: Scoring metric

        Returns:
            Dictionary of cross-validation scores
        """
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)

        return {
            f"{scoring}_mean": scores.mean(),
            f"{scoring}_std": scores.std(),
            f"{scoring}_min": scores.min(),
            f"{scoring}_max": scores.max(),
            "all_scores": scores.tolist(),
        }

    def evaluate_with_confidence(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_lower: np.ndarray,
        y_upper: np.ndarray,
        confidence_level: float = 0.95,
    ) -> dict[str, float]:
        """
        Evaluate predictions with confidence intervals.

        Args:
            y_true: True target values
            y_pred: Predicted values
            y_lower: Lower confidence bounds
            y_upper: Upper confidence bounds
            confidence_level: Confidence level

        Returns:
            Dictionary of evaluation metrics
        """
        # Check if true values fall within confidence intervals
        within_ci = (y_true >= y_lower) & (y_true <= y_upper)
        coverage = np.mean(within_ci)

        # Confidence interval width
        ci_width = y_upper - y_lower

        return {
            "coverage": coverage,
            "expected_coverage": confidence_level,
            "ci_width_mean": np.mean(ci_width),
            "ci_width_std": np.std(ci_width),
            "coverage_gap": coverage - confidence_level,
        }

    def get_evaluation_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_lower: Optional[np.ndarray] = None,
        y_upper: Optional[np.ndarray] = None,
    ) -> dict[str, Any]:
        """
        Generate comprehensive evaluation report.

        Args:
            y_true: True target values
            y_pred: Predicted values
            y_lower: Lower confidence bounds (optional)
            y_upper: Upper confidence bounds (optional)

        Returns:
            Dictionary with full evaluation report
        """
        metrics = self.calculate_regression_metrics(y_true, y_pred)
        error_dist = self.calculate_error_distribution(y_true, y_pred)

        report = {
            "point_metrics": metrics,
            "error_distribution": error_dist,
        }

        if y_lower is not None and y_upper is not None:
            confidence_metrics = self.evaluate_with_confidence(y_true, y_pred, y_lower, y_upper)
            report["confidence_metrics"] = confidence_metrics

        return report

    def save_evaluation_report(
        self,
        report: dict[str, Any],
        model_name: str,
        version: str = "v1",
    ) -> Path:
        """
        Save evaluation report to disk.

        Args:
            report: Evaluation report dictionary
            model_name: Name of model
            version: Model version

        Returns:
            Path to saved report
        """
        import json

        output_path = self.models_dir / f"{model_name}_{version}_evaluation.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        self.logger.info(f"Saved evaluation report to {output_path}")
        return output_path
