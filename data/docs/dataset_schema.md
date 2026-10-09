# ThermoCare AI Dataset Schema

## Overview

This document describes the dataset schema used by the HeatShield feature engineering pipeline.

## Target Variable

### `ed_visits_heat`
- **Type**: Integer
- **Units**: Count
- **Description**: Daily count of heat-related emergency department visits from UKHSA (UK Health Security Agency)
- **Requirements**: Must be present, cannot have missing values
- **Notes**: Observed counts should never be imputed

## Input Features

### Weather Features
Weather data should be available at daily granularity with the following recommended columns:

| Column | Type | Units | Required | Description |
|--------|------|-------|----------|-------------|
| `date` | Date | N/A | Yes | Date of observation |
| `temp_mean` | Numeric | °C | Yes | Daily mean temperature |
| `temp_max` | Numeric | °C | No | Daily maximum temperature |
| `temp_min` | Numeric | °C | No | Daily minimum temperature |
| `humidity` | Numeric | % | Yes | Daily mean relative humidity |
| `precipitation` | Numeric | mm | No | Daily precipitation |
| `wind_speed` | Numeric | km/h | No | Daily mean wind speed |

### Engineered Features

The pipeline automatically generates the following features:

#### Calendar Features
| Feature | Type | Description |
|---------|------|-------------|
| `month` | Categorical | Month of year (1-12) |
| `day_of_week` | Categorical | Day of week (0=Monday) |
| `is_weekend` | Binary | Is weekend (0/1) |
| `day_of_year` | Numeric | Day of year (1-366) |
| `season` | Categorical | Season (spring/summer/autumn/winter) |

#### Temperature Features
| Feature | Type | Description |
|---------|------|-------------|
| `temp_range` | Numeric | Temperature range (temp_max - temp_min) |
| `is_heatwave` | Binary | Flag for heatwave conditions (temp >= 28°C) |
| `is_extreme_heat` | Binary | Flag for extreme heat (temp > 32°C) |
| `temp_anomaly` | Numeric | Temperature deviation from monthly average |
| `heat_index` | Numeric | Apparent temperature combining heat and humidity |

#### Weather Combination Features
| Feature | Type | Description |
|---------|------|-------------|
| `heat_stress_index` | Numeric | Combined heat and humidity stress indicator |
| `is_drought` | Binary | Flag for dry conditions |
| `in_comfort_zone` | Binary | Flag for comfortable temperature range |

#### Lag Features (Training Only)
Lag features use only past information available before the prediction date:

| Feature | Type | Description |
|---------|------|-------------|
| `ed_visits_lag_1` | Numeric | ED visits from 1 day ago |
| `ed_visits_lag_2` | Numeric | ED visits from 2 days ago |
| `ed_visits_lag_3` | Numeric | ED visits from 3 days ago |
| `ed_visits_lag_7` | Numeric | ED visits from 7 days ago (weekly pattern) |

#### Rolling Features (Training Only)
Rolling features use only past data up to the current date:

| Feature | Type | Description |
|---------|------|-------------|
| `ed_visits_rolling_mean_3` | Numeric | 3-day rolling mean of ED visits |
| `ed_visits_rolling_mean_7` | Numeric | 7-day rolling mean of ED visits |
| `ed_visits_rolling_mean_14` | Numeric | 14-day rolling mean of ED visits |
| `temp_rolling_mean_3` | Numeric | 3-day rolling mean of temperature |
| `temp_rolling_mean_7` | Numeric | 7-day rolling mean of temperature |
| `temp_rolling_mean_14` | Numeric | 14-day rolling mean of temperature |

## Data Requirements

### Training Data
- **Minimum**: ~95 daily observations (current target dataset size)
- **Recommended**: At least 1 year of daily data for robust seasonal patterns
- **Date Range**: Should cover multiple heatwave events
- **Target**: Must be complete (no missing values)

### Inference Data
- Must include all required weather features
- Calendar features are derived from date
- Target is not required (for prediction)

## Data Quality Requirements

### Required Columns
- `date`: Date column (required)
- `temp_mean`: Mean temperature (required for training)
- `humidity`: Relative humidity (required for training)
- `ed_visits_heat`: Target column (required for training)

### Expected Data Types
- Date columns: datetime64[ns]
- Numeric columns: float64 or int64
- Categorical columns: object or category

### Missing Data Strategy
- **Weather features**: Mean imputation (configurable via `missing_weather_strategy`)
- **Target features**: NEVER imputed - must be observed counts
- **Calendar features**: Derived from date, no missing values expected

## Data Validation

The pipeline includes comprehensive validation:

1. **Structure Validation**: Required columns present
2. **Type Validation**: Correct data types
3. **Target Validation**: No missing target values
4. **Leakage Prevention**: Date ordering, no future data contamination
5. **Feature Validation**: All engineered features present

## Feature Engineering Pipeline

The pipeline follows this order to prevent leakage:

1. **Sort by date** - Ensures proper time ordering
2. **Create calendar features** - No leakage risk
3. **Create temperature features** - Uses only weather data
4. **Create weather combination features** - Uses only weather data
5. **Create lag features** - Uses only past target values
6. **Create rolling features** - Uses only past target values

## Configuration

Configuration is controlled via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TEMPERATURE_COLUMN` | Mean temperature column | `temp_mean` |
| `TEMP_MAX_COLUMN` | Max temperature column | `temp_max` |
| `TEMP_MIN_COLUMN` | Min temperature column | `temp_min` |
| `HUMIDITY_COLUMN` | Humidity column | `humidity` |
| `HEATWAVE_TEMP_THRESHOLD` | Heatwave temperature threshold | 28.0 |
| `MISSING_WEATHER_STRATEGY` | Strategy for missing weather data | `mean` |
| `LAG_DAYS` | Lag days to create | `[1, 2, 3, 7]` |
| `ROLLING_WINDOWS` | Rolling window sizes | `[3, 7, 14]` |

## Example Data Format

```csv
date,temp_mean,temp_max,temp_min,humidity,precipitation,wind_speed,ed_visits_heat
2023-06-01,25.5,31.2,20.1,65.0,0.0,12.5,105
2023-06-02,26.8,32.5,21.3,62.0,0.0,10.2,112
2023-06-03,27.2,33.1,22.0,60.0,0.0,8.5,118
```

After feature engineering, the dataset expands to include all engineered features:

```csv
date,month,day_of_week,season,is_weekend,temp_range,is_heatwave,ed_visits_lag_1,ed_visits_rolling_mean_3,...
2023-06-01,6,3,spring,0,11.1,0,,,
2023-06-02,6,4,spring,0,11.2,0,105.0,105.0,
2023-06-03,6,5,spring,0,11.1,0,112.0,108.5,
```

## Notes

1. **Current Dataset Size**: ~95 daily observations may not be sufficient for a robust general admissions model
2. **Extreme Heat Forecasting**: Limited data for extreme heat events may affect forecast reliability
3. **Feature Engineering**: All transformations are fitted only on training data to prevent data leakage
4. **Temporal Leakage**: Pipeline includes validation to ensure no future data contamination
