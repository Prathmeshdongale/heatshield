"""
Resource planning service for ThermoCare AI.

This module provides advanced resource planning and optimization functionality.
"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from app.schemas.forecast import ForecastRequest
from app.schemas.hospital import HospitalDemandProjection

logger = logging.getLogger(__name__)


class ResourcePlanner:
    """Service for optimized resource planning during heat events."""

    _instance: Optional["ResourcePlanner"] = None

    def __new__(cls):
        """Singleton pattern for ResourcePlanner."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize ResourcePlanner."""
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls) -> "ResourcePlanner":
        """Get the singleton instance of ResourcePlanner."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def plan_resources(
        self,
        demand_projection: HospitalDemandProjection,
        current_resources: dict[str, int],
        lead_time_hours: int = 24,
    ) -> dict[str, int]:
        """
        Plan resource allocation based on demand projection.

        Args:
            demand_projection: HospitalDemandProjection with projected demand
            current_resources: Current available resources
            lead_time_hours: Lead time for resource allocation

        Returns:
            Dictionary of resources to allocate
        """
        self.logger.info(f"Planning resources for {demand_projection.location}")

        # Calculate resource gap
        resource_gap = demand_projection.resource_gap

        # Calculate allocation based on lead time
        allocation_multiplier = min(1.0, lead_time_hours / 48)  # Max allocation over 48 hours

        return {
            "additional_beds": max(0, int(resource_gap * allocation_multiplier)),
            "additional_staff": max(0, int(resource_gap * allocation_multiplier * 0.5)),
            "equipment_units": max(0, int(resource_gap * allocation_multiplier * 0.2)),
        }

    def optimize_shift_schedule(
        self,
        demand_forecast: list[dict],
        staff_capacity: int,
    ) -> list[dict]:
        """
        Optimize staff shift schedule based on demand forecast.

        Args:
            demand_forecast: List of demand predictions
            staff_capacity: Available staff capacity

        Returns:
            List of optimized shift schedules
        """
        self.logger.info("Optimizing shift schedule")

        # Placeholder: simple allocation
        schedules = []
        for i, forecast in enumerate(demand_forecast):
            shift_demand = forecast.get("demand", 100)
            staff_needed = min(shift_demand // 20, staff_capacity)
            schedules.append({
                "shift": i,
                "start_time": f"{8 + i * 8}:00",
                "staff_needed": staff_needed,
                "coverage": staff_needed / max(1, shift_demand // 20),
            })
        return schedules

    def calculate_resource_efficiency(
        self,
        actual_resources: dict[str, int],
        predicted_demand: float,
        actual_demand: float,
    ) -> dict[str, float]:
        """
        Calculate resource efficiency metrics.

        Args:
            actual_resources: Resources actually used
            predicted_demand: Predicted demand
            actual_demand: Actual demand

        Returns:
            Dictionary of efficiency metrics
        """
        self.logger.info("Calculating resource efficiency")

        efficiency = {}
        for resource, actual in actual_resources.items():
            predicted = predicted_demand * 0.01  # Placeholder ratio
            if predicted > 0:
                efficiency[f"{resource}_utilization"] = actual / predicted
            if actual > 0:
                efficiency[f"{resource}_overspend"] = (actual - actual_demand * 0.01) / actual

        return efficiency

    def get_scenario_forecasts(
        self,
        base_request: ForecastRequest,
        temperature_scenarios: list[float],
    ) -> list[dict]:
        """
        Generate forecasts for multiple temperature scenarios.

        Args:
            base_request: Base ForecastRequest
            temperature_scenarios: List of temperature scenarios

        Returns:
            List of scenario forecasts
        """
        self.logger.info(f"Generating {len(temperature_scenarios)} scenario forecasts")

        scenarios = []
        for temp in temperature_scenarios:
            scenario_request = ForecastRequest(
                date=base_request.date,
                location=base_request.location,
                temperature=temp,
                humidity=base_request.humidity,
                weather_condition=base_request.weather_condition,
            )
            scenarios.append({
                "temperature": temp,
                "request": scenario_request,
            })
        return scenarios
