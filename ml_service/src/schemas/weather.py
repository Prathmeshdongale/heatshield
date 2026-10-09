"""Weather data schemas."""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WeatherMetrics(BaseModel):
    temperature:   Annotated[float, Field(description="°C")]
    humidity:      Annotated[float, Field(description="%")]
    wind_speed:    Annotated[float, Field(description="km/h")]
    wind_direction:Annotated[int,   Field(description="degrees")]
    pressure:      Annotated[float, Field(description="hPa")]
    precipitation: Annotated[float, Field(description="mm")]
    uv_index:      Annotated[float, Field(description="UV index")]


class WeatherData(BaseModel):
    location:      Annotated[str,          Field(description="Location ID")]
    timestamp:     Annotated[datetime,     Field(description="Observation time")]
    metrics:       Annotated[WeatherMetrics, Field(description="Measurements")]
    source:        Annotated[str,          Field(description="Data source")]
    quality_score: Annotated[float,        Field(default=1.0)]


class WeatherRequest(BaseModel):
    location:         str
    start_date:       datetime
    end_date:         datetime
    include_forecast: bool = False


class WeatherResponse(BaseModel):
    location: str
    data:     List[WeatherData]
    metadata: Dict[str, Any]
