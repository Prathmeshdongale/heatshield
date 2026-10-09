"""
test_risk.py — unit tests for the shared risk calculation module.
No mocking needed — pure functions.
"""

import pytest
from app.services.risk import calculate_risk, calculate_risk_from_pct


class TestCalculateRisk:
    def test_green_below_70(self):
        assert calculate_risk(100, 200) == "green"   # 50 %

    def test_amber_at_70(self):
        assert calculate_risk(140, 200) == "amber"   # 70 %

    def test_amber_below_85(self):
        assert calculate_risk(160, 200) == "amber"   # 80 %

    def test_red_at_85(self):
        assert calculate_risk(170, 200) == "red"     # 85 %

    def test_red_below_100(self):
        assert calculate_risk(190, 200) == "red"     # 95 %

    def test_critical_at_100(self):
        assert calculate_risk(200, 200) == "critical"  # 100 %

    def test_critical_over_100(self):
        assert calculate_risk(220, 200) == "critical"  # 110 %

    def test_unknown_when_capacity_none(self):
        assert calculate_risk(50.0, None) == "unknown"

    def test_unknown_when_capacity_zero(self):
        assert calculate_risk(50.0, 0) == "unknown"

    def test_unknown_when_negative_admissions(self):
        assert calculate_risk(-1.0, 200) == "unknown"

    def test_zero_admissions_is_green(self):
        assert calculate_risk(0.0, 200) == "green"


class TestCalculateRiskFromPct:
    def test_green(self):
        assert calculate_risk_from_pct(50.0) == "green"

    def test_amber(self):
        assert calculate_risk_from_pct(75.0) == "amber"

    def test_red(self):
        assert calculate_risk_from_pct(90.0) == "red"

    def test_critical(self):
        assert calculate_risk_from_pct(101.0) == "critical"

    def test_unknown_none(self):
        assert calculate_risk_from_pct(None) == "unknown"

    def test_unknown_negative(self):
        assert calculate_risk_from_pct(-1.0) == "unknown"
