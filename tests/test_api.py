"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_status" in data


def test_health_check_model_status():
    """Test health check includes model status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_status"] in ["ready", "not_loaded"]


def test_model_status_endpoint():
    """Test model status endpoint."""
    response = client.get("/api/v1/model/status")
    # Expected to return 503 since no model is loaded
    assert response.status_code in [200, 503]


def test_api_root():
    """Test API root returns 404 (no endpoint at /)."""
    response = client.get("/")
    assert response.status_code == 404


def test_openapi_schema():
    """Test OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "components" in data


def test_api_docs():
    """Test API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "html" in response.text.lower()


def test_predict_endpoint_no_model():
    """Test prediction endpoint without model."""
    response = client.post(
        "/api/v1/forecast",
        json={
            "date": "2023-08-15",
            "location": "London",
            "temperature": 30.0,
            "humidity": 60.0,
            "weather_condition": "hot",
        },
    )
    # Expected to fail since no model is loaded
    assert response.status_code in [422, 503, 500]


def test_weather_endpoint():
    """Test weather data endpoint."""
    response = client.post(
        "/api/v1/weather",
        json={
            "location": "London",
            "start_date": "2023-08-01T00:00:00",
            "end_date": "2023-08-15T00:00:00",
            "include_forecast": False,
        },
    )
    # Expected to return 500 since weather API is not configured
    assert response.status_code == 500


def test_invalid_forecast_request():
    """Test forecast request with invalid data."""
    response = client.post(
        "/api/v1/forecast",
        json={
            "date": "2023-08-15",
            "location": "London",
            "temperature": 100.0,  # Invalid temperature
            "humidity": 60.0,
            "weather_condition": "hot",
        },
    )
    assert response.status_code == 422


def test_rapidoc_docs():
    """Test rapidoc documentation is available."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "html" in response.text.lower()
