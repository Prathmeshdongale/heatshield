"""
test_capacity_service.py — unit tests for capacity_service.
All Supabase calls and settings are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services import capacity_service

def _demo_settings():
    s = MagicMock()
    s.demo_mode = True
    return s


def _live_settings():
    s = MagicMock()
    s.demo_mode = False
    return s


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

class TestListHospitalsDemoMode:
    def test_returns_hospitals(self):
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            hospitals, source = capacity_service.list_hospitals()
        assert len(hospitals) > 0

    def test_source_is_demo(self):
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            _, source = capacity_service.list_hospitals()
        assert source == "demo"

    def test_risk_status_present_and_valid(self):
        valid = {"green", "amber", "red", "critical", "unknown"}
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            hospitals, _ = capacity_service.list_hospitals()
        for h in hospitals:
            assert h["risk_status"] in valid

    def test_risk_recalculated_from_occupancy(self):
        """risk_status must be derived from occupancy_pct, not blindly copied."""
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            hospitals, _ = capacity_service.list_hospitals()
        for h in hospitals:
            occ = h["occupancy_pct"]
            expected = capacity_service._ensure_risk({"occupancy_pct": occ})["risk_status"]
            assert h["risk_status"] == expected


class TestGetHospitalDemoMode:
    def test_known_id(self):
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            hospital, source = capacity_service.get_hospital("H001")
        assert hospital is not None
        assert hospital["hospital_id"] == "H001"
        assert source == "demo"

    def test_unknown_id_returns_none(self):
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            hospital, _ = capacity_service.get_hospital("ZZZZ")
        assert hospital is None

    def test_case_insensitive(self):
        with patch("app.services.capacity_service.get_settings", return_value=_demo_settings()):
            hospital, _ = capacity_service.get_hospital("h001")
        assert hospital is not None


# ---------------------------------------------------------------------------
# Live mode — repository is mocked
# ---------------------------------------------------------------------------

_LIVE_HOSPITAL = {
    "hospital_id": "H001",
    "name": "Test Hospital",
    "region": "Test Region",
    "address": "1 Test St",
    "latitude": 51.5,
    "longitude": -0.1,
    "contact_email": "test@test.nhs",
    "capacity_total": 200,
    "capacity_available": 50,
    "occupancy_pct": 75.0,
    "risk_status": "amber",
}


class TestListHospitalsLiveMode:
    def test_delegates_to_repository(self):
        with patch("app.services.capacity_service.get_settings", return_value=_live_settings()), \
             patch("app.services.capacity_service.fetch_all_hospitals", return_value=[_LIVE_HOSPITAL]):
            hospitals, source = capacity_service.list_hospitals()
        assert len(hospitals) == 1
        assert source == "live"

    def test_risk_recalculated_live(self):
        h = dict(_LIVE_HOSPITAL, occupancy_pct=90.0, risk_status="green")  # stale DB value
        with patch("app.services.capacity_service.get_settings", return_value=_live_settings()), \
             patch("app.services.capacity_service.fetch_all_hospitals", return_value=[h]):
            hospitals, _ = capacity_service.list_hospitals()
        assert hospitals[0]["risk_status"] == "red"  # recalculated, not "green"


class TestGetHospitalLiveMode:
    def test_found(self):
        with patch("app.services.capacity_service.get_settings", return_value=_live_settings()), \
             patch("app.services.capacity_service.fetch_hospital_by_id", return_value=_LIVE_HOSPITAL):
            hospital, source = capacity_service.get_hospital("H001")
        assert hospital is not None
        assert source == "live"

    def test_not_found(self):
        with patch("app.services.capacity_service.get_settings", return_value=_live_settings()), \
             patch("app.services.capacity_service.fetch_hospital_by_id", return_value=None):
            hospital, source = capacity_service.get_hospital("ZZZZ")
        assert hospital is None
