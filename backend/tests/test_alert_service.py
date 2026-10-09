"""
test_alert_service.py — unit tests for alert_service.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services import alert_service


def _settings(demo=True):
    s = MagicMock()
    s.demo_mode = demo
    return s


_HOSPITAL = {
    "hospital_id": "H001",
    "name": "Test Hospital [DEMO]",
    "region": "Test",
    "capacity_total": 300,
}

_FORECAST_RED = {
    "hospital_id": "H001",
    "model_version": "v-test",
    "generated_at": "2026-10-09T08:00:00Z",
    "days_requested": 7,
    "points": [
        {
            "forecast_date": "2026-10-10",
            "predicted_admissions": 260.0,
            "confidence_lower": 220.0,
            "confidence_upper": 300.0,
            "risk_status": "red",
        },
        {
            "forecast_date": "2026-10-11",
            "predicted_admissions": 180.0,
            "confidence_lower": 150.0,
            "confidence_upper": 210.0,
            "risk_status": "green",   # should NOT generate an alert
        },
        {
            "forecast_date": "2026-10-12",
            "predicted_admissions": 310.0,
            "confidence_lower": 270.0,
            "confidence_upper": 350.0,
            "risk_status": "critical",
        },
    ],
}


class TestListAlertsDemoMode:
    def test_returns_demo_source(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=True)):
            _, source = alert_service.list_alerts()
        assert source == "demo"

    def test_returns_list(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=True)):
            alerts, _ = alert_service.list_alerts()
        assert isinstance(alerts, list)

    def test_filter_by_hospital(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=True)):
            alerts, _ = alert_service.list_alerts(hospital_id="H002")
        for a in alerts:
            assert a["hospital_id"] == "H002"


class TestListAlertsLiveMode:
    def test_generates_alerts_for_red_and_critical(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=False)), \
             patch("app.services.alert_service.fetch_all_hospitals", return_value=[_HOSPITAL]), \
             patch("app.services.alert_service.fetch_forecast", return_value=_FORECAST_RED):
            alerts, source = alert_service.list_alerts()
        assert source == "live"
        assert len(alerts) == 2  # red + critical, not green

    def test_no_alert_for_green(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=False)), \
             patch("app.services.alert_service.fetch_all_hospitals", return_value=[_HOSPITAL]), \
             patch("app.services.alert_service.fetch_forecast", return_value=_FORECAST_RED):
            alerts, _ = alert_service.list_alerts()
        dates = [a["forecast_date"] for a in alerts]
        assert "2026-10-11" not in dates

    def test_severity_mapping(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=False)), \
             patch("app.services.alert_service.fetch_all_hospitals", return_value=[_HOSPITAL]), \
             patch("app.services.alert_service.fetch_forecast", return_value=_FORECAST_RED):
            alerts, _ = alert_service.list_alerts()
        by_date = {a["forecast_date"]: a for a in alerts}
        assert by_date["2026-10-10"]["severity"] == "high"
        assert by_date["2026-10-12"]["severity"] == "critical"

    def test_alert_required_fields(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=False)), \
             patch("app.services.alert_service.fetch_all_hospitals", return_value=[_HOSPITAL]), \
             patch("app.services.alert_service.fetch_forecast", return_value=_FORECAST_RED):
            alerts, _ = alert_service.list_alerts()
        for a in alerts:
            for field in ("alert_id", "hospital_id", "hospital_name", "severity",
                          "message", "triggered_at", "forecast_date", "resolved"):
                assert field in a, f"Missing field '{field}'"

    def test_empty_on_exception(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=False)), \
             patch("app.services.alert_service.fetch_all_hospitals", side_effect=RuntimeError("db down")):
            alerts, _ = alert_service.list_alerts()
        assert alerts == []


class TestListAlertsFilter:
    def test_filter_applied_in_live_mode(self):
        with patch("app.services.alert_service.get_settings", return_value=_settings(demo=False)), \
             patch("app.services.alert_service.fetch_hospital_by_id", return_value=_HOSPITAL), \
             patch("app.services.alert_service.fetch_forecast", return_value=_FORECAST_RED):
            alerts, _ = alert_service.list_alerts(hospital_id="H001")
        for a in alerts:
            assert a["hospital_id"] == "H001"
