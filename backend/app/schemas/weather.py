"""
weather.py — Pydantic schemas for weather observations.

WeatherPoint is one day's observation or forecast.
heat_index_c is the "feels like" temperature accounting for humidity.
"""

from datetime import date
from pydantic import BaseModel, Field
from app.schemas.common import DataStatus


class WeatherPoint(BaseModel):
    observation_date: date = Field(..., examples=["2026-10-09"])
    temperature_max_c: float = Field(..., examples=[34.2])
    temperature_min_c: float = Field(..., examples=[22.1])
    humidity_pct: float = Field(..., ge=0, le=100, examples=[68.0])
    heat_index_c: float = Field(..., examples=[38.5])
    condition: str = Field(..., examples=["Heatwave"])


class WeatherResponse(BaseModel):
    hospital_id: str = Field(..., examples=["H001"])
    days_requested: int = Field(..., examples=[7])
    observations: list[WeatherPoint]


class WeatherEnvelope(BaseModel):
    data: WeatherResponse
    status: DataStatus = DataStatus()
