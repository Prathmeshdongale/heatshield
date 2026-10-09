"""
alert.py — Pydantic schemas for capacity-risk alerts.

Alerts are generated when a hospital's forecast crosses a risk threshold.
severity mirrors RiskStatus but is scoped to the alert record itself.
"""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import DataStatus


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Alert(BaseModel):
    alert_id: str = Field(..., examples=["ALT-0042"])
    hospital_id: str = Field(..., examples=["H001"])
    hospital_name: str = Field(..., examples=["City General Hospital"])
    severity: AlertSeverity = Field(..., examples=["high"])
    message: str = Field(..., examples=["Predicted admissions exceed 85% capacity on 2026-10-12"])
    triggered_at: datetime = Field(..., examples=["2026-10-09T06:00:00Z"])
    forecast_date: str = Field(..., examples=["2026-10-12"])
    resolved: bool = Field(False, examples=[False])


class AlertListResponse(BaseModel):
    data: list[Alert]
    meta: dict
    status: DataStatus = DataStatus()
