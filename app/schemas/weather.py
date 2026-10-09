"""
Weather schemas for ThermoCare AI.

This module defines Pydantic models for weather data API requests and responses.
"""

from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class WeatherMetrics(BaseModel):
    """Weather metrics for a single observation."""

    temperature: Annotated[float, Field(description="Temperature in Celsius")]
    humidity: Annotated[float, Field(description="Relative humidity (%)")]
    wind_speed: Annotated[float, Field(description="Wind speed in km/h")]
    wind_direction: Annotated[int, Field(description="Wind direction in degrees")]
    pressure: Annotated[float, Field(description="Atmospheric pressure in hPa")]
    precipitation: Annotated[float, Field(description="Precipitation in mm")]
    uv_index: Annotated[float, Field(description="UV index")]


class WeatherData(BaseModel):
    """Weather data for a location and timestamp."""

    location: Annotated[str, Field(description="Location identifier")]
    timestamp: Annotated[datetime, Field(description="Observation timestamp")]
    metrics: Annotated[WeatherMetrics, Field(description="Weather metrics")]
    source: Annotated[str, Field(description="Data source identifier")]
    quality_score: Annotated[float, Field(description="Data quality score (0-1)")] = Field(default=1.0)


class WeatherRequest(BaseModel):
    """Request model for weather data fetch."""

    location: Annotated[str, Field(description="Location identifier")]
    start_date: Annotated[datetime, Field(description="Start date for historical data")]
    end_date: Annotated[datetime, Field(description="End date for historical data")]
    include_forecast: Annotated[bool, Field(description="Include weather forecast")] = Field(default=False)


class WeatherResponse(BaseModel):
    """Response model for weather data fetch."""

    location: Annotated[str, Field(description="Location identifier")]
    data: Annotated[list[WeatherData], Field(description="Weather observations")]
    metadata: Annotated[dict[str, Any], Field(description="Response metadata")]


class WeatherAlert(BaseModel):
    """Weather alert model for extreme conditions."""

    alert_type: Annotated[str, Field(description="Alert type identifier")]
    severity: Annotated[str, Field(description="Alert severity: low, medium, high, critical")]
    location: Annotated[str, Field(description="Affected location")]
    start_time: Annotated[datetime, Field(description="Alert start time")]
    end_time: Annotated[datetime, Field(description="Alert end time")]
    description: Annotated[str, Field(description="Alert description")]


class WeatherStation(BaseModel):
    """Weather station metadata."""

    station_id: Annotated[str, Field(description="Station identifier")]
    name: Annotated[str, Field(description="Station name")]
    location: Annotated[str, Field(description="Station location")]
    latitude: Annotated[float, Field(description="Latitude")]
    longitude: Annotated[float, Field(description="Longitude")]
    elevation: Annotated[float, Field(description="Elevation in meters")]
    active: Annotated[bool, Field(description="Is station active")]
