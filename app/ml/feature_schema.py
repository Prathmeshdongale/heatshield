"""
Feature schema definition for HeatShield.

This module defines the target and feature columns with metadata including units,
data types, and descriptions for documentation and validation purposes.
"""

from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FeatureMetadata(BaseModel):
    """Metadata for a single feature column."""

    name: Annotated[str, Field(description="Feature column name")]
    type: Annotated[str, Field(description="Data type (numeric, categorical, date)")]
    units: Annotated[Optional[str], Field(description="Units of measurement")]
    description: Annotated[str, Field(description="Feature description")]
    is_target: Annotated[bool, Field(description="Is this the target variable")]
    is_required: Annotated[bool, Field(description="Is this column required")]
    source: Annotated[Optional[str], Field(description="Data source")]


class TargetSchema(BaseModel):
    """Schema definition for the target variable."""

    name: Annotated[str, Field(description="Target column name")]
    type: Annotated[str, Field(description="Target type")]
    units: Annotated[str, Field(description="Units of measurement")]
    description: Annotated[str, Field(description="Target description")]


class FeatureSchema(BaseModel):
    """Complete feature schema for the model."""

    target: Annotated[TargetSchema, Field(description="Target variable schema")]
    weather_features: Annotated[List[FeatureMetadata], Field(description="Weather-related features")]
    calendar_features: Annotated[List[FeatureMetadata], Field(description="Calendar/time features")]
    lag_features: Annotated[List[FeatureMetadata], Field(description="Lag features")]
    rolling_features: Annotated[List[FeatureMetadata], Field(description="Rolling statistics features")]
    derived_features: Annotated[List[FeatureMetadata], Field(description="Derived/transformed features")]

    @property
    def all_feature_names(self) -> List[str]:
        """Get all feature column names."""
        return (
            [f.name for f in self.weather_features]
            + [f.name for f in self.calendar_features]
            + [f.name for f in self.lag_features]
            + [f.name for f in self.rolling_features]
            + [f.name for f in self.derived_features]
        )

    @property
    def required_feature_names(self) -> List[str]:
        """Get required feature column names."""
        required = []
        required.extend([f.name for f in self.weather_features if f.is_required])
        required.extend([f.name for f in self.calendar_features if f.is_required])
        required.extend([f.name for f in self.lag_features if f.is_required])
        required.extend([f.name for f in self.rolling_features if f.is_required])
        required.extend([f.name for f in self.derived_features if f.is_required])
        return required

    def get_feature_by_name(self, name: str) -> Optional[FeatureMetadata]:
        """Get feature metadata by name."""
        for feature_list in [
            self.weather_features,
            self.calendar_features,
            self.lag_features,
            self.rolling_features,
            self.derived_features,
        ]:
            for feature in feature_list:
                if feature.name == name:
                    return feature
        return None


def get_heatshield_feature_schema() -> FeatureSchema:
    """
    Get the default HeatShield feature schema.

    This schema defines all features used in the model including:
    - Target: Daily heat-related emergency department counts
    - Weather features: Temperature, humidity, precipitation, wind
    - Calendar features: Date-based features for seasonality
    - Lag features: Previous day counts
    - Rolling features: Rolling statistics
    - Derived features: Heatwave indicators, temperature ranges
    """
    return FeatureSchema(
        target=TargetSchema(
            name="ed_visits_heat",
            type="integer",
            units="count",
            description="Daily count of heat-related emergency department visits from UKHSA",
        ),
        weather_features=[
            FeatureMetadata(
                name="temp_mean",
                type="numeric",
                units="°C",
                description="Daily mean temperature",
                is_target=False,
                is_required=True,
                source="Weather provider (Met Office, OpenWeatherMap, etc.)",
            ),
            FeatureMetadata(
                name="temp_max",
                type="numeric",
                units="°C",
                description="Daily maximum temperature",
                is_target=False,
                is_required=False,
                source="Weather provider",
            ),
            FeatureMetadata(
                name="temp_min",
                type="numeric",
                units="°C",
                description="Daily minimum temperature",
                is_target=False,
                is_required=False,
                source="Weather provider",
            ),
            FeatureMetadata(
                name="temp_range",
                type="numeric",
                units="°C",
                description="Temperature range (max - min)",
                is_target=False,
                is_required=False,
                source="Derived from temp_max and temp_min",
            ),
            FeatureMetadata(
                name="humidity",
                type="numeric",
                units="%",
                description="Daily mean relative humidity",
                is_target=False,
                is_required=True,
                source="Weather provider",
            ),
            FeatureMetadata(
                name="precipitation",
                type="numeric",
                units="mm",
                description="Daily precipitation",
                is_target=False,
                is_required=False,
                source="Weather provider",
            ),
            FeatureMetadata(
                name="wind_speed",
                type="numeric",
                units="km/h",
                description="Daily mean wind speed",
                is_target=False,
                is_required=False,
                source="Weather provider",
            ),
            FeatureMetadata(
                name="is_heatwave",
                type="categorical",
                units="binary",
                description="Flag indicating heatwave conditions",
                is_target=False,
                is_required=False,
                source="Derived from temperature thresholds",
            ),
        ],
        calendar_features=[
            FeatureMetadata(
                name="month",
                type="categorical",
                units="integer",
                description="Month of year",
                is_target=False,
                is_required=True,
                source="Extracted from date",
            ),
            FeatureMetadata(
                name="day_of_week",
                type="categorical",
                units="integer",
                description="Day of week (0=Monday)",
                is_target=False,
                is_required=True,
                source="Extracted from date",
            ),
            FeatureMetadata(
                name="is_weekend",
                type="categorical",
                units="binary",
                description="Is weekend",
                is_target=False,
                is_required=True,
                source="Derived from day_of_week",
            ),
            FeatureMetadata(
                name="day_of_year",
                type="numeric",
                units="integer",
                description="Day of year",
                is_target=False,
                is_required=True,
                source="Extracted from date",
            ),
            FeatureMetadata(
                name="season",
                type="categorical",
                units="string",
                description="Season (spring/summer/autumn/winter)",
                is_target=False,
                is_required=True,
                source="Derived from month",
            ),
        ],
        lag_features=[
            FeatureMetadata(
                name="ed_visits_lag_1",
                type="numeric",
                units="count",
                description="ED visits from 1 day ago",
                is_target=False,
                is_required=False,
                source="Lagged target variable",
            ),
            FeatureMetadata(
                name="ed_visits_lag_2",
                type="numeric",
                units="count",
                description="ED visits from 2 days ago",
                is_target=False,
                is_required=False,
                source="Lagged target variable",
            ),
            FeatureMetadata(
                name="ed_visits_lag_3",
                type="numeric",
                units="count",
                description="ED visits from 3 days ago",
                is_target=False,
                is_required=False,
                source="Lagged target variable",
            ),
            FeatureMetadata(
                name="ed_visits_lag_7",
                type="numeric",
                units="count",
                description="ED visits from 7 days ago (weekly pattern)",
                is_target=False,
                is_required=False,
                source="Lagged target variable",
            ),
        ],
        rolling_features=[
            FeatureMetadata(
                name="ed_visits_rolling_mean_3",
                type="numeric",
                units="count",
                description="3-day rolling mean of ED visits",
                is_target=False,
                is_required=False,
                source="Rolling statistics",
            ),
            FeatureMetadata(
                name="ed_visits_rolling_mean_7",
                type="numeric",
                units="count",
                description="7-day rolling mean of ED visits",
                is_target=False,
                is_required=False,
                source="Rolling statistics",
            ),
            FeatureMetadata(
                name="ed_visits_rolling_mean_14",
                type="numeric",
                units="count",
                description="14-day rolling mean of ED visits",
                is_target=False,
                is_required=False,
                source="Rolling statistics",
            ),
            FeatureMetadata(
                name="temp_rolling_mean_7",
                type="numeric",
                units="°C",
                description="7-day rolling mean of temperature",
                is_target=False,
                is_required=False,
                source="Rolling statistics",
            ),
        ],
        derived_features=[
            FeatureMetadata(
                name="temp_anomaly",
                type="numeric",
                units="°C",
                description="Temperature deviation from monthly average",
                is_target=False,
                is_required=False,
                source="Derived from temperature and month",
            ),
            FeatureMetadata(
                name="heat_index",
                type="numeric",
                units="°C",
                description="Apparent temperature (heat + humidity)",
                is_target=False,
                is_required=False,
                source="Derived from temp_mean and humidity",
            ),
            FeatureMetadata(
                name="is_extreme_heat",
                type="categorical",
                units="binary",
                description="Flag for extreme heat conditions (temp > 32°C)",
                is_target=False,
                is_required=False,
                source="Derived from temperature threshold",
            ),
        ],
    )


def get_feature_list_for_model() -> List[str]:
    """
    Get the exact feature list used by the fitted model.

    This function defines the final feature set after all transformations.
    The order is important and must be preserved during training and inference.
    """
    schema = get_heatshield_feature_schema()
    
    return (
        [schema.target.name]
        + schema.weather_features[0].name  # temp_mean (first required)
        + [f.name for f in schema.weather_features if not f.is_required]
        + schema.calendar_features[0].name  # month (first required)
        + [f.name for f in schema.calendar_features if not f.is_required]
        + [f.name for f in schema.lag_features if f.is_required]
        + [f.name for f in schema.rolling_features if f.is_required]
        + [f.name for f in schema.derived_features if f.is_required]
    )


def get_feature_order_schema() -> Dict[str, str]:
    """
    Get a dictionary mapping feature names to their data types.

    This is used for validation during inference to ensure correct feature ordering.
    """
    schema = get_heatshield_feature_schema()
    
    feature_types = {}
    
    for f in schema.weather_features:
        feature_types[f.name] = f.type
    for f in schema.calendar_features:
        feature_types[f.name] = f.type
    for f in schema.lag_features:
        feature_types[f.name] = f.type
    for f in schema.rolling_features:
        feature_types[f.name] = f.type
    for f in schema.derived_features:
        feature_types[f.name] = f.type
    
    feature_types[schema.target.name] = schema.target.type
    
    return feature_types
