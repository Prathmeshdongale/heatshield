"""
hospital.py — Pydantic schemas for hospital capacity data.

RiskStatus mirrors what the ML team produces per hospital per forecast window.
  green   → capacity comfortable
  amber   → approaching threshold (≥70 % occupied)
  red     → high risk            (≥85 % occupied)
  critical→ over capacity        (≥100 %)
"""

from enum import Enum
from pydantic import BaseModel, Field
from app.schemas.common import DataStatus


class RiskStatus(str, Enum):
    green = "green"
    amber = "amber"
    red = "red"
    critical = "critical"


class HospitalSummary(BaseModel):
    """Compact representation used in list responses."""
    hospital_id: str = Field(..., examples=["H001"])
    name: str = Field(..., examples=["City General Hospital"])
    region: str = Field(..., examples=["Greater London"])
    capacity_total: int = Field(..., ge=1, examples=[300])
    capacity_available: int = Field(..., ge=0, examples=[72])
    occupancy_pct: float = Field(..., ge=0, le=100, examples=[76.0])
    risk_status: RiskStatus = Field(..., examples=["amber"])


class HospitalDetail(HospitalSummary):
    """Full hospital record returned by the detail endpoint."""
    address: str = Field(..., examples=["1 Hospital Road, London, E1 1AA"])
    latitude: float = Field(..., examples=[51.5074])
    longitude: float = Field(..., examples=[-0.1278])
    contact_email: str = Field(..., examples=["ops@citygeneraldemo.nhs"])


class HospitalListResponse(BaseModel):
    data: list[HospitalSummary]
    meta: dict
    status: DataStatus = DataStatus()


class HospitalDetailResponse(BaseModel):
    data: HospitalDetail
    status: DataStatus = DataStatus()
