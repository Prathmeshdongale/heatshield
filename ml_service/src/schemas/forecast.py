"""Forecast request/response schemas."""

from datetime import date, datetime
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, field_validator


class ForecastRequest(BaseModel):
    date:              Annotated[date,  Field(description="Forecast date")]
    location:          Annotated[str,   Field(description="Trust ID or region")]
    temperature:       Annotated[float, Field(description="Max temperature °C")]
    humidity:          Annotated[float, Field(description="Relative humidity 0-100")]
    weather_condition: Annotated[str,   Field(description="Weather condition string")]

    @field_validator("temperature")
    @classmethod
    def validate_temp(cls, v: float) -> float:
        if not -50 <= v <= 60:
            raise ValueError("Temperature must be -50 to 60 °C")
        return v

    @field_validator("humidity")
    @classmethod
    def validate_humidity(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("Humidity must be 0-100 %")
        return v


class ForecastResponse(BaseModel):
    date:             Annotated[date,     Field(description="Forecast date")]
    location:         Annotated[str,      Field(description="Location")]
    predicted_demand: Annotated[float,    Field(description="Predicted A&E attendances")]
    confidence_lower: Annotated[float,    Field(description="Lower CI bound")]
    confidence_upper: Annotated[float,    Field(description="Upper CI bound")]
    risk_level:       Annotated[str,      Field(description="low/medium/high/critical")]
    generated_at:     Annotated[datetime, Field(description="When forecast was generated")]
    model_version:    Annotated[str,      Field(description="Model version")]

    @field_validator("risk_level")
    @classmethod
    def validate_risk(cls, v: str) -> str:
        valid = ["low", "medium", "high", "critical"]
        if v not in valid:
            raise ValueError(f"risk_level must be one of {valid}")
        return v


class ForecastBatchRequest(BaseModel):
    dates:             List[date]
    location:          str
    temperature:       float
    humidity:          float
    weather_condition: str


class ForecastBatchResponse(BaseModel):
    forecasts:     List[ForecastResponse]
    total_count:   int
    success_count: int
    failed_count:  int


class ForecastError(BaseModel):
    error:     str
    message:   str
    timestamp: datetime
