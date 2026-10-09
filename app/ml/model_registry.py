"""
Model registry for ThermoCare AI.

This module provides functionality for model versioning, loading, and management.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from joblib import dump, load

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Class for managing ML model versions and lifecycle."""

    _instance: Optional["ModelRegistry"] = None

    def __new__(cls, models_dir: Optional[str] = None):
        """Singleton pattern for ModelRegistry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, models_dir: Optional[str] = None):
        """Initialize ModelRegistry."""
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self.models_dir = Path(models_dir or "data/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Model storage
        self._model: Optional[object] = None
        self._model_info: Optional[dict] = None
        self._model_version: Optional[str] = None

    @classmethod
    def get_instance(cls, models_dir: Optional[str] = None) -> "ModelRegistry":
        """Get the singleton instance of ModelRegistry."""
        if cls._instance is None:
            cls._instance = cls(models_dir=models_dir)
        return cls._instance

    def load_model(self, model_path: Path) -> object:
        """
        Load a model from disk.

        Args:
            model_path: Path to model file

        Returns:
            Loaded model
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.logger.info(f"Loading model from {model_path}")
        model = load(model_path)
        self._model = model
        return model

    def load_latest_model(self) -> bool:
        """
        Load the latest model from the models directory.

        Returns:
            True if successful, False otherwise
        """
        # Find latest model file
        model_files = list(self.models_dir.glob("*.joblib"))

        if not model_files:
            self.logger.warning("No model files found in models directory")
            return False

        # Sort by modification time and get latest
        latest_file = max(model_files, key=lambda f: f.stat().mtime)

        try:
            self.load_model(latest_file)
            self._model_version = latest_file.stem.split("_")[-1]
            self._model_info = self._load_model_info(latest_file)
            self.logger.info(f"Loaded latest model: {latest_file.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model {latest_file.name}: {e}")
            return False

    def is_model_loaded(self) -> bool:
        """
        Check if a model is currently loaded.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None

    def get_model(self) -> Optional[object]:
        """
        Get the currently loaded model.

        Returns:
            Loaded model or None
        """
        return self._model

    def get_model_version(self) -> Optional[str]:
        """
        Get the version of the loaded model.

        Returns:
            Model version string or None
        """
        return self._model_version

    def get_model_info(self) -> Optional[dict]:
        """
        Get information about the loaded model.

        Returns:
            Model information dictionary or None
        """
        if self._model_info:
            return {
                "status": "ready",
                "version": self._model_version,
                **self._model_info,
            }
        return None

    def _load_model_info(self, model_path: Path) -> Optional[dict]:
        """
        Load model information from companion file.

        Args:
            model_path: Path to model file

        Returns:
            Model information dictionary
        """
        info_path = model_path.with_suffix(".json")

        if info_path.exists():
            try:
                with open(info_path) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load model info: {e}")

        return {}

    def save_model(self, model: object, version: str, metadata: Optional[dict] = None) -> Path:
        """
        Save a model to disk.

        Args:
            model: Trained model
            version: Model version
            metadata: Optional metadata to save

        Returns:
            Path to saved model
        """
        model_filename = f"model_{version}.joblib"
        model_path = self.models_dir / model_filename

        dump(model, model_path)

        # Save metadata
        if metadata is None:
            metadata = {}
        metadata["version"] = version
        metadata["saved_at"] = str(Path(__file__).parent.name)

        info_path = model_path.with_suffix(".json")
        with open(info_path, "w") as f:
            json.dump(metadata, f, indent=2)

        self.logger.info(f"Saved model version {version} to {model_path}")

        return model_path

    def list_available_models(self) -> list[dict]:
        """
        List all available models.

        Returns:
            List of model information dictionaries
        """
        models = []
        for model_file in self.models_dir.glob("*.joblib"):
            info = self._load_model_info(model_file)
            info["path"] = str(model_file)
            info["filename"] = model_file.name
            models.append(info)
        return models

    def delete_model(self, version: str) -> bool:
        """
        Delete a specific model version.

        Args:
            version: Model version to delete

        Returns:
            True if successful, False otherwise
        """
        model_path = self.models_dir / f"model_{version}.joblib"
        info_path = model_path.with_suffix(".json")

        if model_path.exists():
            try:
                model_path.unlink()
                if info_path.exists():
                    info_path.unlink()
                self.logger.info(f"Deleted model version {version}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to delete model {version}: {e}")

        return False
