"""
Hospital service for ThermoCare AI.

This module provides hospital demand projection and resource planning functionality.
"""

import logging
from typing import Optional

from app.ml.model_registry import ModelRegistry
from app.schemas.forecast import ForecastRequest
from app.schemas.hospital import HospitalDemandProjection, ResourceRecommendation
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


class HospitalService:
    """Service for hospital demand projection and resource planning."""

    _instance: Optional["HospitalService"] = None

    def __new__(cls):
        """Singleton pattern for HospitalService."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize HospitalService."""
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls) -> "HospitalService":
        """Get the singleton instance of HospitalService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def project_demand(
        self,
        request: ForecastRequest,
        forecast_service: ForecastService,
        model_registry: ModelRegistry,
    ) -> HospitalDemandProjection:
        """
        Project hospital demand based on forecast.

        Args:
            request: ForecastRequest with location and weather parameters
            forecast_service: ForecastService for generating forecasts
            model_registry: ModelRegistry with loaded model

        Returns:
            HospitalDemandProjection with projected metrics
        """
        self.logger.info(f"Projecting hospital demand for {request.location}")

        # Generate forecast
        forecast = await forecast_service.generate_forecast(request, model_registry)

        # Convert demand to hospital metrics
        # Placeholder: use simple conversion factors
        projected_ae = forecast.predicted_demand * 1.5
        projected_admissions = forecast.predicted_demand * 0.3

        return HospitalDemandProjection(
            location=request.location,
            date=forecast.date,
            projected_a&e=projected_ae,
            projected_admissions=projected_admissions,
            peak_date=forecast.date,
            peak_a&e=projected_ae,
            resource_gap=max(0, projected_admissions - 100),  # Assuming 100 baseline capacity
            alert_level=self._determine_alert_level(projected_admissions),
        )

    async def get_resource_recommendations(
        self,
        request: ForecastRequest,
        forecast_service: ForecastService,
        model_registry: ModelRegistry,
    ) -> ResourceRecommendation:
        """
        Get resource allocation recommendations.

        Args:
            request: ForecastRequest with location and weather parameters
            forecast_service: ForecastService for generating forecasts
            model_registry: ModelRegistry with loaded model

        Returns:
            ResourceRecommendation with resource requirements
        """
        self.logger.info(f"Generating resource recommendations for {request.location}")

        # Get demand projection
        demand = await self.project_demand(request, forecast_service, model_registry)

        # Calculate resource needs
        additional_beds = int(demand.resource_gap)
        additional_staff = int(additional_beds * 0.5)
        priority = self._determine_priority(demand.alert_level)

        return ResourceRecommendation(
            location=request.location,
            date=demand.date,
            additional_beds=max(0, additional_beds),
            additional_staff=max(0, additional_staff),
            equipment_recommendations=self._get_equipment_recommendations(priority),
            priority=priority,
        )

    def _determine_alert_level(self, admissions: float) -> str:
        """
        Determine alert level based on admissions.

        Args:
            admissions: Projected admissions

        Returns:
            Alert level string: normal, warning, or critical
        """
        if admissions < 100:
            return "normal"
        elif admissions < 500:
            return "warning"
        else:
            return "critical"

    def _determine_priority(self, alert_level: str) -> int:
        """
        Determine priority level from alert level.

        Args:
            alert_level: Alert level string

        Returns:
            Priority level (1-5, 1 highest)
        """
        priorities = {"normal": 5, "warning": 3, "critical": 1}
        return priorities.get(alert_level, 3)

    def _get_equipment_recommendations(self, priority: int) -> list[str]:
        """
        Get equipment recommendations based on priority.

        Args:
            priority: Priority level

        Returns:
            List of equipment recommendations
        """
        if priority == 1:
            return ["ventilators", "infusion pumps", "monitoring equipment"]
        elif priority == 2:
            return ["monitoring equipment", "infusion pumps"]
        else:
            return ["monitoring equipment"]
