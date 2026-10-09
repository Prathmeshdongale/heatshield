"""
Data loader module for ThermoCare AI.

This module provides functionality for loading raw data from various sources.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class DataLoader:
    """Class for loading raw data from files and external sources."""

    def __init__(self, raw_data_dir: Optional[str] = None):
        """
        Initialize DataLoader.

        Args:
            raw_data_dir: Path to raw data directory (optional)
        """
        self.raw_data_dir = Path(raw_data_dir or settings.raw_data_path)
        self.logger = logging.getLogger(__name__)

        # Ensure raw data directory exists
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def load_csv(self, filename: str) -> pd.DataFrame:
        """
        Load data from a CSV file.

        Args:
            filename: Name of the CSV file

        Returns:
            DataFrame with loaded data
        """
        file_path = self.raw_data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.logger.info(f"Loading data from {file_path}")
        return pd.read_csv(file_path)

    def load_weather_data(self) -> pd.DataFrame:
        """
        Load weather data.

        Returns:
            DataFrame with weather data
        """
        return self.load_csv("weather_data.csv")

    def load_healthcare_data(self) -> pd.DataFrame:
        """
        Load healthcare utilization data.

        Returns:
            DataFrame with healthcare data
        """
        return self.load_csv("healthcare_data.csv")

    def load_demographic_data(self) -> pd.DataFrame:
        """
        Load demographic data.

        Returns:
            DataFrame with demographic data
        """
        return self.load_csv("demographics.csv")

    def load_all_data(self) -> dict[str, pd.DataFrame]:
        """
        Load all required data files.

        Returns:
            Dictionary mapping data types to DataFrames
        """
        data = {}
        try:
            data["weather"] = self.load_weather_data()
            data["healthcare"] = self.load_healthcare_data()
            data["demographics"] = self.load_demographic_data()
        except FileNotFoundError as e:
            self.logger.warning(f"Missing data file: {e}")
        return data

    def list_available_files(self) -> list[str]:
        """
        List available data files in raw directory.

        Returns:
            List of filenames
        """
        if not self.raw_data_dir.exists():
            return []

        return [f.name for f in self.raw_data_dir.glob("*.csv")]

    def validate_data_files(self, required_files: list[str]) -> dict[str, bool]:
        """
        Validate that required data files exist.

        Args:
            required_files: List of required filenames

        Returns:
            Dictionary mapping filenames to existence boolean
        """
        return {f: (self.raw_data_dir / f).exists() for f in required_files}
