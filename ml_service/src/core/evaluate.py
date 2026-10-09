"""
evaluate.py — Model evaluation: regression metrics, cross-validation, CI coverage.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
)
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate healthcare demand forecasting models."""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = Path(models_dir or "")

    # ── Point metrics ─────────────────────────────────────────────────────────

    def calculate_regression_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, float]:
        metrics: Dict[str, float] = {
            "mae":   mean_absolute_error(y_true, y_pred),
            "rmse":  float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "r2":    r2_score(y_true, y_pred),
            "mape":  mean_absolute_percentage_error(y_true, y_pred)
                     if np.any(y_true != 0) else 0.0,
            "medae": median_absolute_error(y_true, y_pred),
        }
        mean_true = np.mean(y_true)
        if mean_true != 0:
            metrics["nmse"]      = metrics["rmse"] / mean_true
            metrics["mae_ratio"] = metrics["mae"]  / mean_true
        return metrics

    def calculate_error_distribution(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, float]:
        errors = y_true - y_pred
        return {
            "mean_error":   float(np.mean(errors)),
            "std_error":    float(np.std(errors)),
            "min_error":    float(np.min(errors)),
            "max_error":    float(np.max(errors)),
            "median_error": float(np.median(errors)),
            "p95_error":    float(np.percentile(errors, 95)),
            "p5_error":     float(np.percentile(errors, 5)),
        }

    def calculate_skill_scores(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_baseline: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        metrics = self.calculate_regression_metrics(y_true, y_pred)
        if y_baseline is not None:
            bm = self.calculate_regression_metrics(y_true, y_baseline)
            metrics["r2_improvement"]   = metrics["r2"]   - bm["r2"]
            metrics["mae_improvement"]  = bm["mae"]       - metrics["mae"]
            metrics["rmse_improvement"] = bm["rmse"]      - metrics["rmse"]
            if bm["r2"] != 1:
                metrics["skill_score"] = (metrics["r2"] - bm["r2"]) / (1 - bm["r2"])
        return metrics

    # ── Cross-validation ──────────────────────────────────────────────────────

    def cross_validate_model(
        self,
        model: Any,
        X: pd.DataFrame,
        y: pd.Series,
        cv: int = 5,
        scoring: str = "r2",
    ) -> Dict[str, Any]:
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
        return {
            f"{scoring}_mean":  float(scores.mean()),
            f"{scoring}_std":   float(scores.std()),
            f"{scoring}_min":   float(scores.min()),
            f"{scoring}_max":   float(scores.max()),
            "all_scores":       scores.tolist(),
        }

    # ── CI coverage ───────────────────────────────────────────────────────────

    def evaluate_with_confidence(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_lower: np.ndarray,
        y_upper: np.ndarray,
        confidence_level: float = 0.95,
    ) -> Dict[str, float]:
        within = (y_true >= y_lower) & (y_true <= y_upper)
        ci_width = y_upper - y_lower
        return {
            "coverage":          float(np.mean(within)),
            "expected_coverage": confidence_level,
            "ci_width_mean":     float(np.mean(ci_width)),
            "ci_width_std":      float(np.std(ci_width)),
            "coverage_gap":      float(np.mean(within)) - confidence_level,
        }

    # ── Full report ───────────────────────────────────────────────────────────

    def get_evaluation_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_lower: Optional[np.ndarray] = None,
        y_upper: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "point_metrics":    self.calculate_regression_metrics(y_true, y_pred),
            "error_distribution": self.calculate_error_distribution(y_true, y_pred),
        }
        if y_lower is not None and y_upper is not None:
            report["confidence_metrics"] = self.evaluate_with_confidence(
                y_true, y_pred, y_lower, y_upper
            )
        return report

    def save_evaluation_report(
        self, report: Dict[str, Any], model_name: str, version: str = "v1"
    ) -> Path:
        output_path = self.models_dir / f"{model_name}_{version}_evaluation.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("Saved evaluation report to %s", output_path)
        return output_path
