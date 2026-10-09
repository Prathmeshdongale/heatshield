"""
feature_schema.py — Pydantic schema describing every feature used by the model.
Useful for documentation, validation and contract enforcement.
"""

from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureMetadata(BaseModel):
    name:        Annotated[str,           Field(description="Feature column name")]
    type:        Annotated[str,           Field(description="Data type (numeric, categorical, date)")]
    units:       Annotated[Optional[str], Field(description="Units of measurement")]
    description: Annotated[str,           Field(description="Feature description")]
    is_target:   Annotated[bool,          Field(description="Is this the target variable")]
    is_required: Annotated[bool,          Field(description="Is this column required")]
    source:      Annotated[Optional[str], Field(description="Data source")]


class TargetSchema(BaseModel):
    name:        Annotated[str, Field(description="Target column name")]
    type:        Annotated[str, Field(description="Target type")]
    units:       Annotated[str, Field(description="Units")]
    description: Annotated[str, Field(description="Target description")]


class FeatureSchema(BaseModel):
    target:           Annotated[TargetSchema,           Field(description="Target variable")]
    weather_features: Annotated[List[FeatureMetadata],  Field(description="Weather features")]
    calendar_features:Annotated[List[FeatureMetadata],  Field(description="Calendar features")]
    lag_features:     Annotated[List[FeatureMetadata],  Field(description="Lag features")]
    rolling_features: Annotated[List[FeatureMetadata],  Field(description="Rolling features")]
    derived_features: Annotated[List[FeatureMetadata],  Field(description="Derived features")]

    @property
    def all_feature_names(self) -> List[str]:
        lists = [self.weather_features, self.calendar_features,
                 self.lag_features, self.rolling_features, self.derived_features]
        return [f.name for group in lists for f in group]

    @property
    def required_feature_names(self) -> List[str]:
        lists = [self.weather_features, self.calendar_features,
                 self.lag_features, self.rolling_features, self.derived_features]
        return [f.name for group in lists for f in group if f.is_required]

    def get_feature_by_name(self, name: str) -> Optional[FeatureMetadata]:
        for group in [self.weather_features, self.calendar_features,
                      self.lag_features, self.rolling_features, self.derived_features]:
            for f in group:
                if f.name == name:
                    return f
        return None


def get_heatshield_feature_schema() -> FeatureSchema:
    """Return the canonical feature schema for HeatShield."""
    return FeatureSchema(
        target=TargetSchema(
            name="ed_visits_heat", type="integer", units="count",
            description="Daily count of heat-related ED visits (UKHSA)",
        ),
        weather_features=[
            FeatureMetadata(name="temp_mean",  type="numeric", units="°C",
                description="Daily mean temperature", is_target=False, is_required=True, source="Weather provider"),
            FeatureMetadata(name="temp_max",   type="numeric", units="°C",
                description="Daily max temperature",  is_target=False, is_required=False, source="Weather provider"),
            FeatureMetadata(name="temp_min",   type="numeric", units="°C",
                description="Daily min temperature",  is_target=False, is_required=False, source="Weather provider"),
            FeatureMetadata(name="temp_range", type="numeric", units="°C",
                description="Temperature range",      is_target=False, is_required=False, source="Derived"),
            FeatureMetadata(name="humidity",   type="numeric", units="%",
                description="Daily mean humidity",    is_target=False, is_required=True,  source="Weather provider"),
            FeatureMetadata(name="precipitation", type="numeric", units="mm",
                description="Daily precipitation",    is_target=False, is_required=False, source="Weather provider"),
            FeatureMetadata(name="wind_speed", type="numeric", units="km/h",
                description="Daily mean wind speed",  is_target=False, is_required=False, source="Weather provider"),
            FeatureMetadata(name="is_heatwave", type="categorical", units="binary",
                description="Heatwave flag",          is_target=False, is_required=False, source="Derived"),
        ],
        calendar_features=[
            FeatureMetadata(name="month",       type="categorical", units="integer",
                description="Month of year",           is_target=False, is_required=True, source="date"),
            FeatureMetadata(name="day_of_week", type="categorical", units="integer",
                description="Day of week (0=Monday)", is_target=False, is_required=True, source="date"),
            FeatureMetadata(name="is_weekend",  type="categorical", units="binary",
                description="Weekend flag",            is_target=False, is_required=True, source="day_of_week"),
            FeatureMetadata(name="day_of_year", type="numeric",     units="integer",
                description="Day of year",             is_target=False, is_required=True, source="date"),
            FeatureMetadata(name="season",      type="categorical", units="string",
                description="Season",                  is_target=False, is_required=True, source="month"),
        ],
        lag_features=[
            FeatureMetadata(name="ed_visits_lag_1", type="numeric", units="count",
                description="ED visits 1 day ago", is_target=False, is_required=False, source="Lagged target"),
            FeatureMetadata(name="ed_visits_lag_2", type="numeric", units="count",
                description="ED visits 2 days ago", is_target=False, is_required=False, source="Lagged target"),
            FeatureMetadata(name="ed_visits_lag_3", type="numeric", units="count",
                description="ED visits 3 days ago", is_target=False, is_required=False, source="Lagged target"),
            FeatureMetadata(name="ed_visits_lag_7", type="numeric", units="count",
                description="ED visits 7 days ago (weekly pattern)",
                is_target=False, is_required=False, source="Lagged target"),
        ],
        rolling_features=[
            FeatureMetadata(name="ed_visits_rolling_mean_3",  type="numeric", units="count",
                description="3-day rolling mean ED visits",  is_target=False, is_required=False, source="Rolling"),
            FeatureMetadata(name="ed_visits_rolling_mean_7",  type="numeric", units="count",
                description="7-day rolling mean ED visits",  is_target=False, is_required=False, source="Rolling"),
            FeatureMetadata(name="ed_visits_rolling_mean_14", type="numeric", units="count",
                description="14-day rolling mean ED visits", is_target=False, is_required=False, source="Rolling"),
            FeatureMetadata(name="temp_rolling_mean_7",       type="numeric", units="°C",
                description="7-day rolling mean temperature",is_target=False, is_required=False, source="Rolling"),
        ],
        derived_features=[
            FeatureMetadata(name="temp_anomaly",    type="numeric", units="°C",
                description="Temp deviation from monthly avg", is_target=False, is_required=False, source="Derived"),
            FeatureMetadata(name="heat_index",      type="numeric", units="°C",
                description="Apparent temperature",           is_target=False, is_required=False, source="Derived"),
            FeatureMetadata(name="is_extreme_heat", type="categorical", units="binary",
                description="Extreme heat flag (>32°C)",      is_target=False, is_required=False, source="Derived"),
        ],
    )


def get_feature_order_schema() -> Dict[str, str]:
    """Return {feature_name: data_type} for all features."""
    schema = get_heatshield_feature_schema()
    result: Dict[str, str] = {}
    for group in [schema.weather_features, schema.calendar_features,
                  schema.lag_features, schema.rolling_features, schema.derived_features]:
        for f in group:
            result[f.name] = f.type
    result[schema.target.name] = schema.target.type
    return result
