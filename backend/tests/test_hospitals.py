"""Tests for GET /api/v1/hospitals and GET /api/v1/hospitals/{id}"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# --- list ---

def test_list_hospitals_200():
    r = client.get("/api/v1/hospitals")
    assert r.status_code == 200


def test_list_hospitals_returns_demo_label():
    r = client.get("/api/v1/hospitals")
    body = r.json()
    assert body["status"]["data_source"] == "demo"


def test_list_hospitals_has_required_fields():
    r = client.get("/api/v1/hospitals")
    hospitals = r.json()["data"]
    assert len(hospitals) > 0
    first = hospitals[0]
    for field in ("hospital_id", "name", "region", "capacity_total",
                  "capacity_available", "occupancy_pct", "risk_status"):
        assert field in first, f"Missing field: {field}"


def test_list_hospitals_meta_count_matches():
    r = client.get("/api/v1/hospitals")
    body = r.json()
    assert body["meta"]["count"] == len(body["data"])


# --- detail ---

def test_get_hospital_detail_200():
    r = client.get("/api/v1/hospitals/H001")
    assert r.status_code == 200


def test_get_hospital_detail_fields():
    r = client.get("/api/v1/hospitals/H001")
    data = r.json()["data"]
    assert data["hospital_id"] == "H001"
    assert "address" in data
    assert "latitude" in data
    assert "longitude" in data


def test_get_hospital_case_insensitive():
    r = client.get("/api/v1/hospitals/h001")
    assert r.status_code == 200


def test_get_hospital_not_found_404():
    r = client.get("/api/v1/hospitals/ZZZZ")
    assert r.status_code == 404


def test_get_hospital_not_found_error_body():
    r = client.get("/api/v1/hospitals/ZZZZ")
    detail = r.json()["detail"]
    assert detail["code"] == "HOSPITAL_NOT_FOUND"
