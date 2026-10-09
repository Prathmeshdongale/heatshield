"""
Forecast schemas for ThermoCare AI.

This module defines Pydantic models for forecasting API requests and responses.
"""

from datetime import date, datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, field_validator


class ForecastRequest(BaseModel):
    """Request model for forecast generation."""

    date: Annotated[date, Field(description="Date for forecast")]
    location: Annotated[str, Field(description="Location identifier (e.g., NHS region)")]
    temperature: Annotated[float, Field(description="Average temperature in Celsius")]
    humidity: Annotated[float, Field(description="Relative humidity (%)")]
    weather_condition: Annotated[str, Field(description="Weather condition identifier")]

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature range."""
        if not -50 <= v <= 60:
            raise ValueError("Temperature must be between -50 and 60 Celsius")
        return v

    @field_validator("humidity")
    @classmethod
    def validate_humidity(cls, v: float) -> float:
        """Validate humidity range."""
        if not 0 <= v <= 100:
            raise ValueError("Humidity must be between 0 and 100 percent")
        return v


class ForecastResponse(BaseModel):
    """Response model for forecast generation."""

    date: Annotated[date, Field(description="Forecast date")]
    location: Annotated[str, Field(description="Location identifier")]
    predicted_demand: Annotated[float, Field(description="Predicted healthcare demand")]
    confidence_lower: Annotated[float, Field(description="Lower confidence bound")]
    confidence_upper: Annotated[float, Field(description="Upper confidence bound")]
    risk_level: Annotated[str, Field(description="Risk level: low, medium, high, critical")]
    generated_at: Annotated[datetime, Field(description="Forecast generation timestamp")]
    model_version: Annotated[str, Field(description="Model version used")]

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level value."""
        valid_levels = ["low", "medium", "high", "critical"]
        if v not in valid_levels:
            raise ValueError(f"Risk level must be one of: {valid_levels}")
        return v


class ForecastError(BaseModel):
    """Error response model for forecast operations."""

    error: Annotated[str, Field(description="Error type")]
    message: Annotated[str, Field(description="Error message")]
    timestamp: Annotated[datetime, Field(description="Error timestamp")]


class ForecastBatchRequest(BaseModel):
    """Request model for batch forecast generation."""

    dates: Annotated[list[date], Field(description="List of dates for forecast")]
    location: Annotated[str, Field(description="Location identifier")]
    temperature: Annotated[float, Field(description="Average temperature in Celsius")]
    humidity: Annotated[float, Field(description="Relative humidity (%)")]
    weather_condition: Annotated[str, Field(description="Weather condition identifier")]


class ForecastBatchResponse(BaseModel):
    """Response model for batch forecast generation."""

    forecasts: Annotated[list[ForecastResponse], Field(description="List of forecasts")]
    total_count: Annotated[int, Field(description="Total number of forecasts")]
    success_count: Annotated[int, Field(description="Number of successful forecasts")]
    failed_count: Annotated[int, Field(description="Number of failed forecasts")]
