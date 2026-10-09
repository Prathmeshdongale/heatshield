"""
data_loader.py — Load raw data from CSV files and other sources.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


class DataLoader:
    """Load raw data from files and external sources."""

    def __init__(self, raw_data_dir: Optional[str] = None):
        self.raw_data_dir = Path(raw_data_dir or settings.raw_data_path)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def load_csv(self, filename: str) -> pd.DataFrame:
        file_path = self.raw_data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        logger.info(f"Loading {file_path}")
        return pd.read_csv(file_path)

    def load_weather_data(self) -> pd.DataFrame:
        return self.load_csv("weather_data.csv")

    def load_healthcare_data(self) -> pd.DataFrame:
        return self.load_csv("healthcare_data.csv")

    def load_demographic_data(self) -> pd.DataFrame:
        return self.load_csv("demographics.csv")

    def load_all_data(self) -> dict[str, pd.DataFrame]:
        data = {}
        for name, loader in [
            ("weather",      self.load_weather_data),
            ("healthcare",   self.load_healthcare_data),
            ("demographics", self.load_demographic_data),
        ]:
            try:
                data[name] = loader()
            except FileNotFoundError as e:
                logger.warning(f"Missing data file: {e}")
        return data

    def list_available_files(self) -> list[str]:
        return [f.name for f in self.raw_data_dir.glob("*.csv")]

    def validate_data_files(self, required_files: list[str]) -> dict[str, bool]:
        return {f: (self.raw_data_dir / f).exists() for f in required_files}
