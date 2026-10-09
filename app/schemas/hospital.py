"""
Hospital schemas for ThermoCare AI.

This module defines Pydantic models for hospital metrics and data.
"""

from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field


class HospitalMetrics(BaseModel):
    """Hospital operational metrics."""

    a&e_visits: Annotated[float, Field(description="A&E visits count")]
    hospital_admissions: Annotated[float, Field(description="Hospital admissions count")]
    bed_occupancy_rate: Annotated[float, Field(description="Bed occupancy rate (%)")]
    staff_availability: Annotated[float, Field(description="Staff availability (%)")]
    average_wait_time: Annotated[float, Field(description="Average wait time in minutes")]
    critical_care_bed_occupancy: Annotated[float, Field(description="Critical care bed occupancy rate (%)")]


class HospitalData(BaseModel):
    """Hospital data for a location and time period."""

    location: Annotated[str, Field(description="Location identifier (e.g., NHS trust)")]
    timestamp: Annotated[datetime, Field(description="Data timestamp")]
    metrics: Annotated[HospitalMetrics, Field(description="Hospital metrics")]
    reference_period: Annotated[str, Field(description="Reference period (e.g., '2023-08')")]


class HospitalDemandProjection(BaseModel):
    """Projected hospital demand."""

    location: Annotated[str, Field(description="Location identifier")]
    date: Annotated[datetime, Field(description="Projection date")]
    projected_a&e: Annotated[float, Field(description="Projected A&E visits")]
    projected_admissions: Annotated[float, Field(description="Projected admissions")]
    peak_date: Annotated[datetime, Field(description="Peak demand date")]
    peak_a&e: Annotated[float, Field(description="Peak A&E visits")]
    resource_gap: Annotated[float, Field(description="Resource gap (demand - capacity)")]
    alert_level: Annotated[str, Field(description="Alert level: normal, warning, critical")]


class ResourceRecommendation(BaseModel):
    """Resource allocation recommendation."""

    location: Annotated[str, Field(description="Location identifier")]
    date: Annotated[datetime, Field(description="Recommendation date")]
    additional_beds: Annotated[int, Field(description="Additional beds needed")]
    additional_staff: Annotated[int, Field(description="Additional staff needed")]
    equipment_recommendations: Annotated[list[str], Field(description="Equipment needed")]
    priority: Annotated[int, Field(description="Priority level (1-5, 1 highest)")]
