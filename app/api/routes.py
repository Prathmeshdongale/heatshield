"""
API routes for ThermoCare AI.

This module defines the API endpoint routes and handlers.
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.ml.model_registry import ModelRegistry
from app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastError
from app.schemas.hospital import HospitalDemandProjection, ResourceRecommendation
from app.schemas.weather import WeatherRequest, WeatherResponse
from app.services.forecast_service import ForecastService
from app.services.hospital_service import HospitalService
from app.services.weather_service import WeatherService

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
api_router = APIRouter(prefix="/api/v1", tags=["api"])


@api_router.get("/health", response_model=dict, summary="Health check")
async def health_check():
    """
    Health check endpoint.

    Returns the application status.
    """
    return {"status": "healthy", "service": "thermocare-ai"}


@api_router.get("/model/status", response_model=dict, summary="Model status")
async def get_model_status(model_registry: ModelRegistry = Depends(ModelRegistry.get_instance)):
    """
    Get model status information.

    Returns model version, training date, and performance metrics.
    """
    if model_registry is None or not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model_registry.get_model_info()


@api_router.post("/forecast", response_model=ForecastResponse, summary="Generate forecast")
async def generate_forecast(
    request: ForecastRequest,
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    model_registry: ModelRegistry = Depends(ModelRegistry.get_instance),
):
    """
    Generate healthcare demand forecast.

    Returns predicted demand with confidence intervals and risk level.
    """
    if model_registry is None or not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        forecast = await forecast_service.generate_forecast(request, model_registry)
        return forecast
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/forecast/batch", response_model=ForecastResponse, summary="Generate batch forecast")
async def generate_batch_forecast(
    forecasts: list[ForecastRequest],
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    model_registry: ModelRegistry = Depends(ModelRegistry.get_instance),
):
    """
    Generate multiple healthcare demand forecasts.

    Processes multiple requests and returns results.
    """
    if model_registry is None or not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        results = await forecast_service.generate_batch_forecast(forecasts, model_registry)
        return results
    except Exception as e:
        logger.error(f"Batch forecast generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/weather", response_model=WeatherResponse, summary="Fetch weather data")
async def fetch_weather_data(
    request: WeatherRequest,
    weather_service: WeatherService = Depends(WeatherService.get_instance),
):
    """
    Fetch weather data for a location and date range.

    Returns historical and forecast weather data.
    """
    try:
        weather_data = await weather_service.fetch_weather_data(request)
        return weather_data
    except Exception as e:
        logger.error(f"Weather data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/hospital/demand", response_model=HospitalDemandProjection, summary="Project hospital demand")
async def project_hospital_demand(
    request: ForecastRequest,
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    hospital_service: HospitalService = Depends(HospitalService.get_instance),
    model_registry: ModelRegistry = Depends(ModelRegistry.get_instance),
):
    """
    Project hospital demand based on forecast.

    Returns projected admissions, A&E visits, and resource gaps.
    """
    if model_registry is None or not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        demand = await hospital_service.project_demand(request, forecast_service, model_registry)
        return demand
    except Exception as e:
        logger.error(f"Hospital demand projection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/hospital/resources", response_model=ResourceRecommendation, summary="Get resource recommendations")
async def get_resource_recommendations(
    location: str,
    date: date,
    forecast_service: ForecastService = Depends(ForecastService.get_instance),
    hospital_service: HospitalService = Depends(HospitalService.get_instance),
    model_registry: ModelRegistry = Depends(ModelRegistry.get_instance),
):
    """
    Get resource allocation recommendations for a location and date.

    Returns recommendations for additional beds, staff, and equipment.
    """
    if model_registry is None or not model_registry.is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        request = ForecastRequest(date=date, location=location, temperature=30.0, humidity=60.0, weather_condition="hot")
        recommendation = await hospital_service.get_resource_recommendations(request, forecast_service, model_registry)
        return recommendation
    except Exception as e:
        logger.error(f"Resource recommendation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
