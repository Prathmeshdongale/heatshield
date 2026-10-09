"""
metrics.py — Pydantic schemas for ML model evaluation metrics.

These are produced by Member 2 (ML team) after model training/evaluation.
Fields must be agreed with the ML team before this schema is finalised.
"""

from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import DataStatus


class ModelMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_version: str = Field(..., examples=["v1.2.0"])
    evaluated_on: date = Field(..., examples=["2026-10-01"])
    mae: float = Field(..., description="Mean Absolute Error (admissions/day)", examples=[3.8])
    rmse: float = Field(..., description="Root Mean Square Error", examples=[5.1])
    r2: float = Field(..., description="R-squared score (0–1)", ge=0, le=1, examples=[0.87])
    training_data_from: date = Field(..., examples=["2023-01-01"])
    training_data_to: date = Field(..., examples=["2026-09-30"])
    feature_count: int = Field(..., ge=1, examples=[12])


class MetricsEnvelope(BaseModel):
    data: ModelMetrics
    status: DataStatus = DataStatus()
