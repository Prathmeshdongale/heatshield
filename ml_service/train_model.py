"""
train_model.py — Train the HeatShield demand-forecasting model on the NHS dataset.

Usage (from ml_service/ directory):
    python train_model.py

Outputs:
    data/models/heatshield_v1.joblib        — trained model artifact
    data/models/heatshield_v1_metrics.json  — evaluation metrics
    data/reports/transformation_stats.json  — pipeline stats

The artifact is also copied to ../backend/ml/artifacts/model.joblib so the
backend can load it immediately.
"""

import json
import logging
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# ── path setup so we can import src.* ─────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("train")

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_FILE    = ROOT / "data" / "raw" / "nhs_heat_hospital_demand.csv"
MODELS_DIR   = ROOT / "data" / "models"
REPORTS_DIR  = ROOT / "data" / "reports"
BACKEND_ARTIFACT = ROOT.parent / "backend" / "ml" / "artifacts" / "model.joblib"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
BACKEND_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)

# ── Feature & target columns (derived from dataset schema) ────────────────────
TARGET = "ae_attendances"           # primary target: daily A&E attendances

FEATURE_COLS = [
    # Weather
    "tmax_c", "tmin_c", "humidity_pct", "heat_index_c",
    "uv_index", "pm25_ugm3", "ozone_ugm3",
    # Heatwave flags
    "warm_night_flag", "consecutive_hot_days", "heatwave_flag",
    # Calendar
    "day_of_week", "is_bank_holiday",
    # Hospital capacity context
    "general_acute_beds", "icu_beds", "ambulances_available",
    "baseline_staff_per_shift", "bed_occupancy_pct",
    # Demographics
    "pct_pop_over_65", "pct_pop_under_5", "imd_deprivation_decile",
    "green_space_pct", "ac_cooled_wards_pct",
]

SECONDARY_TARGETS = [
    "emergency_admissions",
    "heat_related_admissions",
    "icu_demand",
    "ambulance_callouts",
]


def load_and_prepare(path: Path) -> pd.DataFrame:
    log.info("Loading dataset from %s", path)
    df = pd.read_csv(path, parse_dates=["date"])
    log.info("  Rows: %d  |  Columns: %d", len(df), len(df.columns))

    # Encode heat_health_alert (categorical)
    alert_map = {"Normal": 0, "Heat-Health Watch": 1, "Heat-Health Alert": 2,
                 "Heat Emergency": 3}
    df["heat_health_alert_enc"] = df["heat_health_alert"].map(alert_map).fillna(0)

    # Month, season, weekend
    df["month"]      = df["date"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["season"]     = df["month"].apply(_season)

    # Lag features (per trust, sorted by date)
    df = df.sort_values(["trust_id", "date"]).reset_index(drop=True)
    for lag in [1, 3, 7]:
        df[f"ae_lag_{lag}"] = df.groupby("trust_id")[TARGET].shift(lag)

    # Rolling means (per trust)
    for window in [3, 7]:
        df[f"ae_roll_{window}"] = (
            df.groupby("trust_id")[TARGET]
            .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
        )

    # Drop rows where lag features are NaN (first few rows per trust)
    df = df.dropna(subset=[f"ae_lag_{lag}" for lag in [1, 3, 7]])
    log.info("  After feature engineering: %d rows", len(df))
    return df


def _season(month: int) -> int:
    return {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
            6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}.get(month, 0)


def build_feature_list() -> list[str]:
    extra = [
        "heat_health_alert_enc", "month", "is_weekend", "season",
        "ae_lag_1", "ae_lag_3", "ae_lag_7",
        "ae_roll_3", "ae_roll_7",
    ]
    return FEATURE_COLS + extra


def train_and_evaluate(df: pd.DataFrame, feature_cols: list[str]) -> tuple:
    X = df[feature_cols].fillna(0).astype(float)
    y = df[TARGET].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    log.info("Train: %d  |  Test: %d", len(X_train), len(X_test))

    models = {
        "random_forest":    RandomForestRegressor(n_estimators=200, max_depth=12,
                                                   random_state=42, n_jobs=-1),
        "gradient_boosting": GradientBoostingRegressor(n_estimators=200, max_depth=6,
                                                        learning_rate=0.05, random_state=42),
        "ridge":            Ridge(alpha=1.0),
    }

    results = {}
    for name, model in models.items():
        log.info("  Training %s ...", name)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = {
            "mae":  float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2":   float(r2_score(y_test, y_pred)),
        }
        log.info("    R²=%.4f  MAE=%.2f  RMSE=%.2f",
                 metrics["r2"], metrics["mae"], metrics["rmse"])
        results[name] = (model, metrics, X_train, X_test, y_train, y_test)

    # Pick best by R²
    best_name = max(results, key=lambda n: results[n][1]["r2"])
    best_model, best_metrics, *_ = results[best_name]
    log.info("Best model: %s  (R²=%.4f)", best_name, best_metrics["r2"])
    return best_model, best_name, best_metrics, feature_cols, results


def save_artifacts(model, name, metrics, feature_cols, all_results):
    # ── Save primary model ─────────────────────────────────────────────────
    model_path = MODELS_DIR / "heatshield_v1.joblib"
    model.version = "v1.0.0"
    dump(model, model_path)
    log.info("Saved model → %s", model_path)

    # ── Save full metrics including all models ─────────────────────────────
    full_metrics = {
        "model_version":      "v1.0.0",
        "best_model":         name,
        "evaluated_on":       pd.Timestamp.today().date().isoformat(),
        "mae":                metrics["mae"],
        "rmse":               metrics["rmse"],
        "r2":                 metrics["r2"],
        "training_data_from": "2024-04-01",
        "training_data_to":   "2025-03-31",
        "feature_count":      len(feature_cols),
        "feature_columns":    feature_cols,
        "target":             TARGET,
        "all_models": {
            n: {"mae": r[1]["mae"], "rmse": r[1]["rmse"], "r2": r[1]["r2"]}
            for n, r in all_results.items()
        },
    }
    metrics_path = MODELS_DIR / "heatshield_v1_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(full_metrics, f, indent=2)
    log.info("Saved metrics → %s", metrics_path)

    # ── Copy artifact to backend ───────────────────────────────────────────
    shutil.copy2(model_path, BACKEND_ARTIFACT)
    log.info("Copied artifact → %s", BACKEND_ARTIFACT)

    # ── Save Supabase-ready metrics row ───────────────────────────────────
    supabase_row = {
        "model_version":       "v1.0.0",
        "evaluated_on":        pd.Timestamp.today().date().isoformat(),
        "mae":                 round(metrics["mae"], 4),
        "rmse":                round(metrics["rmse"], 4),
        "r2":                  round(metrics["r2"], 4),
        "training_data_from":  "2024-04-01",
        "training_data_to":    "2025-03-31",
        "feature_count":       len(feature_cols),
        "data_status":         "live",
    }
    supabase_path = MODELS_DIR / "supabase_metrics_row.json"
    with open(supabase_path, "w") as f:
        json.dump(supabase_row, f, indent=2)
    log.info("Supabase metrics row → %s", supabase_path)

    return model_path


def push_metrics_to_supabase(metrics_row: dict):
    """Push model metrics to Supabase model_metrics table."""
    try:
        import os, httpx
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
        if not url or not key:
            log.warning("Supabase credentials not found — skipping metrics push")
            return
        r = httpx.post(
            f"{url}/rest/v1/model_metrics",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            json=[metrics_row],
            timeout=15,
        )
        if r.status_code in (200, 201, 204):
            log.info("Pushed metrics to Supabase ✓")
        else:
            log.warning("Supabase push returned HTTP %d: %s", r.status_code, r.text[:200])
    except Exception as exc:
        log.warning("Could not push metrics to Supabase: %s", exc)


if __name__ == "__main__":
    log.info("=" * 60)
    log.info("  HeatShield Model Training")
    log.info("=" * 60)

    if not DATA_FILE.exists():
        log.error("Dataset not found: %s", DATA_FILE)
        sys.exit(1)

    # 1. Load and prepare data
    df = load_and_prepare(DATA_FILE)

    # 2. Build feature list
    feature_cols = build_feature_list()
    available = [c for c in feature_cols if c in df.columns]
    missing   = [c for c in feature_cols if c not in df.columns]
    if missing:
        log.warning("Missing columns (excluded): %s", missing)
    feature_cols = available

    # 3. Train
    best_model, best_name, best_metrics, feature_cols, all_results = train_and_evaluate(df, feature_cols)

    # 4. Save artifacts
    save_artifacts(best_model, best_name, best_metrics, feature_cols, all_results)

    # 5. Push metrics to Supabase (reads .env from backend/)
    env_path = ROOT.parent / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                import os; os.environ.setdefault(k.strip(), v.strip())

    supabase_row_path = MODELS_DIR / "supabase_metrics_row.json"
    if supabase_row_path.exists():
        with open(supabase_row_path) as f:
            import json as _json
            push_metrics_to_supabase(_json.load(f))

    log.info("=" * 60)
    log.info("Training complete. Model saved to %s", MODELS_DIR / "heatshield_v1.joblib")
    log.info("Backend artifact: %s", BACKEND_ARTIFACT)
    log.info("=" * 60)
