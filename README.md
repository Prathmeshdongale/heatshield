<<<<<<< HEAD
# ThermoCareAI

ThermoCareAI is a project for [describe your project purpose here].

## Features
- Add project features here.

## Getting Started
1. Clone the repository.
2. Install the required dependencies.
3. Configure environment variables if needed.
4. Run the application using the appropriate command.

## Project Structure

```text
ThermoCareAI/
ÃÄÄ docs/
³   ÀÄÄ api-contract.md
ÃÄÄ .gitignore
ÀÄÄ README.md
```

## Documentation
- [API Contract](docs/api-contract.md)

## License
Add your license information here.
=======
# ThermoCare AI

A standalone machine learning service for forecasting healthcare demand associated with extreme heat in England.

## Overview

ThermoCare AI predicts healthcare demand patterns during extreme heat events using weather data, historical healthcare utilization, and demographic information. The service provides:

- Real-time weather data integration
- Healthcare demand forecasting
- Resource planning recommendations
- RESTful API for integration

## Technology Stack

- **Backend**: FastAPI with Uvicorn
- **ML**: scikit-learn, pandas, NumPy
- **API**: Pydantic for validation
- **Testing**: pytest
- **Deployment Ready**: Docker containerization ready

## Project Structure

```
ThermoCareAI/
├── app/                    # Application code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── schemas/           # Pydantic models
│   │   ├── forecast.py
│   │   ├── weather.py
│   │   └── hospital.py
│   ├── api/               # API routes
│   │   └── routes.py
│   ├── services/          # Business logic
│   │   ├── weather_service.py
│   │   ├── forecast_service.py
│   │   ├── hospital_service.py
│   │   └── resource_planning.py
│   └── ml/                # Machine learning components
│       ├── data_loader.py
│       ├── validation.py
│       ├── preprocessing.py
│       ├── features.py
│       ├── train.py
│       ├── evaluate.py
│       ├── predict.py
│       └── model_registry.py
├── data/                  # Data directories
│   ├── raw/               # Raw datasets
│   ├── interim/           # Intermediate data
│   ├── processed/         # Processed data
│   ├── models/            # Trained models
│   └── reports/           # Generated reports
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
└── .gitignore            # Git ignore rules
```

## Installation (Windows)

### Prerequisites

- Python 3.11 or higher
- PowerShell (for Windows)

### Step 1: Create Virtual Environment

Open PowerShell in the project directory and run:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify activation (prompt should show (venv))
python --version
```

### Step 2: Install Dependencies

With the virtual environment activated:

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### Step 3: Configure Environment

```powershell
# Copy environment example file
Copy-Item .env.example .env

# Edit .env with your configuration (optional - uses defaults)
notepad .env
```

## Development

### Running the Development Server

With the virtual environment activated:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Running Tests

```powershell
# Run all tests
pytest

# Run specific test file
pytest tests/test_health.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v
```

## API Endpoints

### Public Endpoints

- `GET /health` - Health check endpoint (returns application status)
- `GET /api/v1/model/status` - Model status and version information

### Forecasting Endpoints

- `POST /api/v1/forecast` - Generate demand forecast
  ```json
  {
    "date": "2023-08-15",
    "location": "London",
    "temperature": 30.0,
    "humidity": 60.0,
    "weather_condition": "hot"
  }
  ```

- `POST /api/v1/forecast/batch` - Generate multiple forecasts

### Weather Endpoints

- `POST /api/v1/weather` - Fetch weather data

### Hospital Endpoints

- `POST /api/v1/hospital/demand` - Project hospital demand
- `POST /api/v1/hospital/resources` - Get resource recommendations

## Configuration

Environment variables (configured in `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Application environment | `development` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `MODEL_DIR` | Model storage directory | `data/models` |
| `DATA_DIR` | Data directory root | `data` |
| `REPORTS_DIR` | Reports directory | `data/reports` |
| `DEFAULT_LATITUDE` | Default latitude (London) | `51.5074` |
| `DEFAULT_LONGITUDE` | Default longitude (London) | `-0.1278` |
| `DEFAULT_TIMEZONE` | Default timezone | `Europe/London` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["http://localhost:3000", "http://localhost:8080"]` |
| `WEATHER_PROVIDER` | Weather provider | `met_office` |
| `FORECAST_HORIZON_DAYS` | Forecast days | `7` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Environment Variables for Weather Providers

**OpenWeatherMap:**
```
WEATHER_API_BASE_URL=https://api.openweathermap.org/data/2.5
WEATHER_API_KEY=your_api_key_here
```

**VisualCrossing:**
```
WEATHER_API_BASE_URL=https://weather.visualcrossing.com/VisualCrossingWebServices/rest-services
WEATHER_API_KEY=your_api_key_here
```

## Model Pipeline

1. **Data Loading**: Load raw weather and healthcare data
2. **Validation**: Validate data quality and completeness
3. **Preprocessing**: Clean and normalize data
4. **Feature Engineering**: Create predictive features
5. **Training**: Train forecasting models
6. **Evaluation**: Assess model performance
7. **Prediction**: Generate forecasts
8. **Resource Planning**: Recommend resource allocation

## Data Requirements

Raw datasets should include:

- Weather data (temperature, humidity, precipitation)
- Historical healthcare utilization (A&E visits, hospital admissions)
- Demographic information
- Calendar features (season, holidays)

## Important Notes

### Model Status

The application starts **without** a trained model. The API will report:

- `/health`: Model status as "not_loaded"
- `/api/v1/model/status`: Returns model unavailable status
- Prediction endpoints: Return 503 Service Unavailable

This design allows the API to function for health checks and configuration even before model training.

### Adding a Trained Model

To enable predictions:

1. Train a model using the training scripts
2. Save the model to `data/models/` directory
3. The application will automatically load the latest model on startup

## Troubleshooting

### Virtual Environment Issues

```powershell
# Deactivate virtual environment
deactivate

# Remove and recreate
Remove-Item -Recurse -Force venv
python -m venv venv
```

### Permission Errors

```powershell
# Set execution policy for script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependency Installation Issues

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

## License

MIT License
>>>>>>> origin/feature/ml-service
