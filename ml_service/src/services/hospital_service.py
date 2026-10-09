"""hospital_service.py — Hospital demand projection."""

import logging
from typing import Optional

from src.core.model_registry import ModelRegistry
from src.schemas.forecast import ForecastRequest
from src.schemas.hospital import HospitalDemandProjection, ResourceRecommendation
from src.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


class HospitalService:
    _instance: Optional["HospitalService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "HospitalService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def project_demand(
        self,
        request: ForecastRequest,
        forecast_service: ForecastService,
        model_registry: ModelRegistry,
    ) -> HospitalDemandProjection:
        forecast = await forecast_service.generate_forecast(request, model_registry)
        projected_ae         = forecast.predicted_demand * 1.5
        projected_admissions = forecast.predicted_demand * 0.3

        return HospitalDemandProjection(
            location=request.location,
            date=forecast.generated_at,
            projected_ae=round(projected_ae, 1),
            projected_admissions=round(projected_admissions, 1),
            peak_date=forecast.generated_at,
            peak_ae=round(projected_ae, 1),
            resource_gap=max(0.0, projected_admissions - 100),
            alert_level=self._alert(projected_admissions),
        )

    async def get_resource_recommendations(
        self,
        request: ForecastRequest,
        forecast_service: ForecastService,
        model_registry: ModelRegistry,
    ) -> ResourceRecommendation:
        demand = await self.project_demand(request, forecast_service, model_registry)
        priority = {3: 1, 2: 2, 1: 3}.get(
            {"normal": 1, "warning": 2, "critical": 3}.get(demand.alert_level, 1), 3
        )
        return ResourceRecommendation(
            location=request.location,
            date=demand.date,
            additional_beds=max(0, int(demand.resource_gap)),
            additional_staff=max(0, int(demand.resource_gap * 0.5)),
            equipment_recommendations=self._equipment(priority),
            priority=priority,
        )

    @staticmethod
    def _alert(admissions: float) -> str:
        if admissions < 100:  return "normal"
        if admissions < 500:  return "warning"
        return "critical"

    @staticmethod
    def _equipment(priority: int) -> list[str]:
        if priority == 1:
            return ["ventilators", "infusion pumps", "monitoring equipment"]
        if priority == 2:
            return ["monitoring equipment", "infusion pumps"]
        return ["monitoring equipment"]
