"""Hospital demand and resource schemas."""

from datetime import datetime
from typing import Annotated, List
from pydantic import BaseModel, Field


class HospitalDemandProjection(BaseModel):
    location:             Annotated[str,      Field(description="Trust ID")]
    date:                 Annotated[datetime, Field(description="Projection date")]
    projected_ae:         Annotated[float,    Field(description="Projected A&E visits")]
    projected_admissions: Annotated[float,    Field(description="Projected admissions")]
    peak_date:            Annotated[datetime, Field(description="Peak demand date")]
    peak_ae:              Annotated[float,    Field(description="Peak A&E visits")]
    resource_gap:         Annotated[float,    Field(description="Demand minus capacity")]
    alert_level:          Annotated[str,      Field(description="normal/warning/critical")]


class ResourceRecommendation(BaseModel):
    location:                  Annotated[str,       Field(description="Trust ID")]
    date:                      Annotated[datetime,  Field(description="Recommendation date")]
    additional_beds:           Annotated[int,       Field(description="Extra beds needed")]
    additional_staff:          Annotated[int,       Field(description="Extra staff needed")]
    equipment_recommendations: Annotated[List[str], Field(description="Equipment list")]
    priority:                  Annotated[int,       Field(description="1-5, 1=highest")]
