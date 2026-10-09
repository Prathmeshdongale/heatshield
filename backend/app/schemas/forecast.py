"""
forecast.py — Pydantic schemas for demand forecasts.

ForecastPoint is one day's prediction from the ML model.
The `days` query param controls how many points are returned (1–14).
"""

from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import DataStatus


class ForecastPoint(BaseModel):
    forecast_date: date = Field(..., examples=["2026-10-10"])
    predicted_admissions: float = Field(..., ge=0, examples=[42.5])
    confidence_lower: float = Field(..., ge=0, examples=[35.0])
    confidence_upper: float = Field(..., ge=0, examples=[50.0])
    risk_status: str = Field(..., examples=["amber"])


class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    hospital_id: str = Field(..., examples=["H001"])
    model_version: str = Field(..., examples=["v1.2.0"])
    generated_at: str = Field(..., examples=["2026-10-09T08:00:00Z"])
    days_requested: int = Field(..., examples=[7])
    points: list[ForecastPoint]


class ForecastEnvelope(BaseModel):
    data: ForecastResponse
    status: DataStatus = DataStatus()
