"""
capacity_service.py — business logic for hospital capacity.

Responsibilities:
  - Fetch hospitals + latest capacity snapshot from the repository.
  - Compute/validate risk_status using the shared risk module.
  - Normalise field names so the route layer only sees the agreed schema shape.
  - In demo mode, return mock data and label it explicitly.
"""

import logging
from app.config import get_settings
from app.services.risk import calculate_risk_from_pct
from app.repositories.hospital_repository import fetch_all_hospitals, fetch_hospital_by_id
from app.mock_data import HOSPITALS

logger = logging.getLogger(__name__)


class HospitalNotFoundError(ValueError):
    """Raised when a hospital_id does not exist."""


def _ensure_risk(hospital: dict) -> dict:
    """
    Re-derive risk_status from occupancy_pct to ensure it matches the
    agreed thresholds, even if the DB stored a stale value.
    """
    occ = hospital.get("occupancy_pct")
    hospital["risk_status"] = calculate_risk_from_pct(occ)
    return hospital


def list_hospitals() -> tuple[list[dict], str]:
    """
    Returns (hospitals, data_source) where data_source is 'demo' or 'live'.
    Risk status is always recalculated from occupancy_pct.
    """
    settings = get_settings()

    if settings.demo_mode:
        hospitals = [_ensure_risk(dict(h)) for h in HOSPITALS.values()]
        return hospitals, "demo"

    hospitals = fetch_all_hospitals()
    data_source = "demo" if not hospitals else "live"
    return [_ensure_risk(dict(h)) for h in hospitals], data_source


def get_hospital(hospital_id: str) -> tuple[dict | None, str]:
    """
    Returns (hospital_detail, data_source) or (None, 'demo') if not found.
    """
    settings = get_settings()
    hid = hospital_id.upper()

    if settings.demo_mode:
        hospital = HOSPITALS.get(hid)
        if hospital:
            return _ensure_risk(dict(hospital)), "demo"
        return None, "demo"

    hospital = fetch_hospital_by_id(hid)
    if not hospital:
        return None, "live"
    return _ensure_risk(hospital), "live"
