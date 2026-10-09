"""Tests for GET /api/v1/health"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_200():
    r = client.get("/api/v1/health")
    assert r.status_code == 200


def test_health_body():
    r = client.get("/api/v1/health")
    body = r.json()
    assert body["status"] == "ok"
    assert "env" in body
    assert "version" in body
