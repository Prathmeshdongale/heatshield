"""
routes.py — FastAPI routes for the ML Service.
All endpoints under /api/v1
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from src.core.model_registry import ModelRegistry
from src.schemas.forecast import ForecastRequest, ForecastResponse, ForecastBatchResponse
from src.schemas.hospital import HospitalDemandProjection, ResourceRecommendation
from src.schemas.weather import WeatherRequest, WeatherResponse
from src.services.forecast_service import ForecastService
from src.services.hospital_service import HospitalService
from src.services.weather_service import WeatherService

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api/v1", tags=["api"])


# ── Health ────────────────────────────────────────────────────────────────────

@api_router.get("/health", summary="Health check")
async def health_check():
    return {"status": "healthy", "service": "heatshield-ml"}


@api_router.get("/model/status", summary="Model status")
async def get_model_status(
    model_registry: ModelRegistry = Depends(ModelRegistry.get_instance),
):
    if not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model_registry.get_model_info()


# ── Forecast ──────────────────────────────────────────────────────────────────

@api_router.post("/forecast", response_model=ForecastResponse, summary="Generate forecast")
async def generate_forecast(
    request: ForecastRequest,
    forecast_service: ForecastService  = Depends(ForecastService.get_instance),
    model_registry:   ModelRegistry    = Depends(ModelRegistry.get_instance),
):
    if not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        return await forecast_service.generate_forecast(request, model_registry)
    except Exception as exc:
        logger.error("Forecast failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/forecast/batch", response_model=ForecastBatchResponse, summary="Batch forecast")
async def generate_batch_forecast(
    forecasts: list[ForecastRequest],
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    model_registry:   ModelRegistry   = Depends(ModelRegistry.get_instance),
):
    if not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        return await forecast_service.generate_batch_forecast(forecasts, model_registry)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Weather ───────────────────────────────────────────────────────────────────

@api_router.post("/weather", response_model=WeatherResponse, summary="Fetch weather data")
async def fetch_weather(
    request: WeatherRequest,
    weather_service: WeatherService = Depends(WeatherService.get_instance),
):
    try:
        return await weather_service.fetch_weather_data(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Hospital ──────────────────────────────────────────────────────────────────

@api_router.post("/hospital/demand", response_model=HospitalDemandProjection, summary="Project hospital demand")
async def project_hospital_demand(
    request: ForecastRequest,
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    hospital_service: HospitalService = Depends(HospitalService.get_instance),
    model_registry:   ModelRegistry   = Depends(ModelRegistry.get_instance),
):
    if not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        return await hospital_service.project_demand(request, forecast_service, model_registry)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/hospital/resources", response_model=ResourceRecommendation, summary="Resource recommendations")
async def get_resource_recommendations(
    request: ForecastRequest,
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    hospital_service: HospitalService = Depends(HospitalService.get_instance),
    model_registry:   ModelRegistry   = Depends(ModelRegistry.get_instance),
):
    if not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        return await hospital_service.get_resource_recommendations(
            request, forecast_service, model_registry
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
