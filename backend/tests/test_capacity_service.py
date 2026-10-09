"""
test_capacity_service.py — unit tests for capacity_service.
Repository calls are mocked; no demo branching.
"""

import pytest
from unittest.mock import patch
from app.services import capacity_service

_HOSPITAL = {
    "hospital_id": "H001", "name": "Test Hospital", "region": "Test Region",
    "address": "1 Test St", "latitude": 51.5, "longitude": -0.1,
    "contact_email": "test@test.nhs",
    "capacity_total": 200, "capacity_available": 50,
    "occupancy_pct": 75.0, "risk_status": "amber",
}


class TestListHospitals:
    def test_returns_hospitals(self):
        with patch("app.services.capacity_service.fetch_all_hospitals", return_value=[_HOSPITAL]):
            hospitals, source = capacity_service.list_hospitals()
        assert len(hospitals) == 1
        assert hospitals[0]["hospital_id"] == "H001"

    def test_source_is_live(self):
        with patch("app.services.capacity_service.fetch_all_hospitals", return_value=[_HOSPITAL]):
            _, source = capacity_service.list_hospitals()
        assert source == "live"

    def test_risk_recalculated(self):
        h = dict(_HOSPITAL, occupancy_pct=90.0, risk_status="green")
        with patch("app.services.capacity_service.fetch_all_hospitals", return_value=[h]):
            hospitals, _ = capacity_service.list_hospitals()
        assert hospitals[0]["risk_status"] == "red"

    def test_risk_status_valid(self):
        valid = {"green", "amber", "red", "critical", "unknown"}
        with patch("app.services.capacity_service.fetch_all_hospitals", return_value=[_HOSPITAL]):
            hospitals, _ = capacity_service.list_hospitals()
        for h in hospitals:
            assert h["risk_status"] in valid

    def test_propagates_runtime_error(self):
        with patch("app.services.capacity_service.fetch_all_hospitals",
                   side_effect=RuntimeError("DB down")):
            with pytest.raises(RuntimeError):
                capacity_service.list_hospitals()


class TestGetHospital:
    def test_found(self):
        with patch("app.services.capacity_service.fetch_hospital_by_id", return_value=_HOSPITAL):
            hospital, source = capacity_service.get_hospital("H001")
        assert hospital is not None
        assert hospital["hospital_id"] == "H001"
        assert source == "live"

    def test_not_found(self):
        with patch("app.services.capacity_service.fetch_hospital_by_id", return_value=None):
            hospital, source = capacity_service.get_hospital("ZZZZ")
        assert hospital is None
        assert source == "live"

    def test_case_insensitive(self):
        with patch("app.services.capacity_service.fetch_hospital_by_id",
                   return_value=_HOSPITAL) as m:
            capacity_service.get_hospital("h001")
        m.assert_called_with("H001")

    def test_risk_recalculated(self):
        h = dict(_HOSPITAL, occupancy_pct=95.0, risk_status="green")
        with patch("app.services.capacity_service.fetch_hospital_by_id", return_value=h):
            hospital, _ = capacity_service.get_hospital("H001")
        assert hospital["risk_status"] == "red"
