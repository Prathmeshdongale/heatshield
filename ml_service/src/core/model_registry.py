"""
model_registry.py — Model versioning, loading and lifecycle management.
Singleton so a single loaded model is shared across the application.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from joblib import dump, load

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manage ML model versions — singleton per process."""

    _instance: Optional["ModelRegistry"] = None

    def __new__(cls, models_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, models_dir: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True
        self.models_dir = Path(models_dir or "data/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._model: Optional[object] = None
        self._model_info: Optional[Dict[str, Any]] = None
        self._model_version: Optional[str] = None

    @classmethod
    def get_instance(cls, models_dir: Optional[str] = None) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls(models_dir=models_dir)
        return cls._instance

    # ── Load / save ───────────────────────────────────────────────────────────

    def load_model(self, model_path: Path) -> object:
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        logger.info(f"Loading model from {model_path}")
        self._model = load(model_path)
        return self._model

    def load_latest_model(self) -> bool:
        """Load the most-recently modified .joblib file."""
        files = list(self.models_dir.glob("*.joblib"))
        if not files:
            logger.warning("No model files found in %s", self.models_dir)
            return False
        latest = max(files, key=lambda f: f.stat().st_mtime)
        try:
            self.load_model(latest)
            self._model_version = latest.stem.split("_")[-1]
            self._model_info = self._load_model_info(latest)
            logger.info("Loaded latest model: %s", latest.name)
            return True
        except Exception as exc:
            logger.error("Failed to load model %s: %s", latest.name, exc)
            return False

    def save_model(
        self,
        model: object,
        version: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        model_path = self.models_dir / f"model_{version}.joblib"
        dump(model, model_path)
        meta = metadata or {}
        meta["version"] = version
        with open(model_path.with_suffix(".json"), "w") as f:
            json.dump(meta, f, indent=2)
        logger.info("Saved model v%s to %s", version, model_path)
        return model_path

    # ── Queries ───────────────────────────────────────────────────────────────

    def is_model_loaded(self) -> bool:
        return self._model is not None

    def get_model(self) -> Optional[object]:
        return self._model

    def get_model_version(self) -> Optional[str]:
        return self._model_version

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        if self._model_info is not None:
            return {"status": "ready", "version": self._model_version, **self._model_info}
        return None

    def list_available_models(self) -> list[Dict[str, Any]]:
        models = []
        for f in self.models_dir.glob("*.joblib"):
            info = self._load_model_info(f)
            info.update({"path": str(f), "filename": f.name})
            models.append(info)
        return models

    def delete_model(self, version: str) -> bool:
        path = self.models_dir / f"model_{version}.joblib"
        if not path.exists():
            return False
        try:
            path.unlink()
            info_path = path.with_suffix(".json")
            if info_path.exists():
                info_path.unlink()
            logger.info("Deleted model v%s", version)
            return True
        except Exception as exc:
            logger.error("Failed to delete model v%s: %s", version, exc)
            return False

    # ── Private ───────────────────────────────────────────────────────────────

    def _load_model_info(self, model_path: Path) -> Dict[str, Any]:
        info_path = model_path.with_suffix(".json")
        if info_path.exists():
            try:
                with open(info_path) as f:
                    return json.load(f)
            except Exception as exc:
                logger.warning("Could not read model info: %s", exc)
        return {}
