"""Tests for GET /api/v1/metrics"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_200():
    r = client.get("/api/v1/metrics")
    assert r.status_code == 200


def test_metrics_fields():
    data = client.get("/api/v1/metrics").json()["data"]
    for field in ("model_version", "evaluated_on", "mae", "rmse", "r2",
                  "training_data_from", "training_data_to", "feature_count"):
        assert field in data, f"Missing field: {field}"


def test_metrics_r2_in_range():
    data = client.get("/api/v1/metrics").json()["data"]
    assert 0 <= data["r2"] <= 1


def test_metrics_demo_label():
    r = client.get("/api/v1/metrics")
    assert r.json()["status"]["data_source"] == "demo"
