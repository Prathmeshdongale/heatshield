"""Tests for GET /api/v1/metrics"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_METRICS_ROW = {
    "model_version": "v1.2.0-demo", "evaluated_on": "2026-10-01",
    "mae": 3.8, "rmse": 5.1, "r2": 0.87,
    "training_data_from": "2023-01-01", "training_data_to": "2026-09-30",
    "feature_count": 12, "data_status": "demo",
}


def _patch_db(rows=None):
    rows = [_METRICS_ROW] if rows is None else rows
    m = MagicMock()
    m.select.return_value = rows
    return patch("app.repositories.metrics_repository.get_supabase", return_value=m)


def test_metrics_200():
    with _patch_db():
        r = client.get("/api/v1/metrics")
    assert r.status_code == 200


def test_metrics_fields():
    with _patch_db():
        data = client.get("/api/v1/metrics").json()["data"]
    for field in ("model_version", "evaluated_on", "mae", "rmse", "r2",
                  "training_data_from", "training_data_to", "feature_count"):
        assert field in data, f"Missing field: {field}"


def test_metrics_r2_in_range():
    with _patch_db():
        data = client.get("/api/v1/metrics").json()["data"]
    assert 0 <= data["r2"] <= 1


def test_metrics_returns_live_label():
    with _patch_db():
        r = client.get("/api/v1/metrics")
    assert r.json()["status"]["data_source"] == "live"


def test_metrics_503_when_db_down():
    with patch("app.repositories.metrics_repository.get_supabase", return_value=None):
        r = client.get("/api/v1/metrics")
    assert r.status_code == 503


def test_metrics_404_when_no_rows():
    with _patch_db(rows=[]):
        r = client.get("/api/v1/metrics")
    assert r.status_code == 404
