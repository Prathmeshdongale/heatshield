"""Tests for GET /api/v1/hospitals and GET /api/v1/hospitals/{id}"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_HOSPITAL_ROW = {
    "hospital_id": "H001", "name": "City General [TEST]", "region": "Greater London",
    "address": "1 Test Rd", "latitude": 51.5, "longitude": -0.1,
    "contact_email": "test@test.nhs", "capacity_total": 300, "data_status": "demo",
    "capacity_available": 72, "occupancy_pct": 76.0, "risk_status": "amber",
}


def _mock_supabase(hospitals, capacity):
    m = MagicMock()
    def select(table, **kwargs):
        single = kwargs.get("single", False)
        if table == "hospitals":
            return hospitals[0] if single and hospitals else hospitals
        if table == "hospital_capacity":
            return capacity
        return []
    m.select.side_effect = select
    return m


def _patch_db(hospitals=None, capacity=None):
    h = hospitals if hospitals is not None else [_HOSPITAL_ROW]
    c = capacity if capacity is not None else []
    return patch("app.repositories.hospital_repository.get_supabase",
                 return_value=_mock_supabase(h, c))


# ── List ─────────────────────────────────────────────────────────────────────

def test_list_hospitals_200():
    with _patch_db():
        r = client.get("/api/v1/hospitals")
    assert r.status_code == 200


def test_list_hospitals_returns_live_label():
    with _patch_db():
        r = client.get("/api/v1/hospitals")
    assert r.json()["status"]["data_source"] == "live"


def test_list_hospitals_has_required_fields():
    with _patch_db():
        r = client.get("/api/v1/hospitals")
    first = r.json()["data"][0]
    for field in ("hospital_id", "name", "region", "capacity_total",
                  "capacity_available", "occupancy_pct", "risk_status"):
        assert field in first, f"Missing field: {field}"


def test_list_hospitals_meta_count_matches():
    with _patch_db():
        r = client.get("/api/v1/hospitals")
    body = r.json()
    assert body["meta"]["count"] == len(body["data"])


def test_list_hospitals_503_when_db_down():
    with patch("app.repositories.hospital_repository.get_supabase", return_value=None):
        r = client.get("/api/v1/hospitals")
    assert r.status_code == 503


# ── Detail ────────────────────────────────────────────────────────────────────

def test_get_hospital_detail_200():
    with _patch_db():
        r = client.get("/api/v1/hospitals/H001")
    assert r.status_code == 200


def test_get_hospital_detail_fields():
    with _patch_db():
        r = client.get("/api/v1/hospitals/H001")
    data = r.json()["data"]
    assert data["hospital_id"] == "H001"
    assert "address" in data
    assert "latitude" in data


def test_get_hospital_case_insensitive():
    with _patch_db():
        r = client.get("/api/v1/hospitals/h001")
    assert r.status_code == 200


def test_get_hospital_not_found_404():
    m = MagicMock()
    m.select.return_value = None
    with patch("app.repositories.hospital_repository.get_supabase", return_value=m):
        r = client.get("/api/v1/hospitals/ZZZZ")
    assert r.status_code == 404


def test_get_hospital_not_found_error_body():
    m = MagicMock()
    m.select.return_value = None
    with patch("app.repositories.hospital_repository.get_supabase", return_value=m):
        r = client.get("/api/v1/hospitals/ZZZZ")
    assert r.json()["detail"]["code"] == "HOSPITAL_NOT_FOUND"
