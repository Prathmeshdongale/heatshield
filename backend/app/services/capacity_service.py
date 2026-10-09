"""
capacity_service.py — hospital capacity from the real database.
No demo fallback — all data comes from Supabase.
"""

import logging
from app.services.risk import calculate_risk_from_pct
from app.repositories.hospital_repository import fetch_all_hospitals, fetch_hospital_by_id

logger = logging.getLogger(__name__)


class HospitalNotFoundError(ValueError):
    """Raised when a hospital_id does not exist in the DB."""


def _ensure_risk(hospital: dict) -> dict:
    """Re-derive risk_status from occupancy_pct against canonical thresholds."""
    occ = hospital.get("occupancy_pct")
    hospital["risk_status"] = calculate_risk_from_pct(occ)
    return hospital


def list_hospitals() -> tuple[list[dict], str]:
    """Returns (hospitals, 'live'). Raises RuntimeError if DB unreachable."""
    hospitals = fetch_all_hospitals()
    return [_ensure_risk(dict(h)) for h in hospitals], "live"


def get_hospital(hospital_id: str) -> tuple[dict | None, str]:
    """Returns (hospital, 'live'). Returns (None, 'live') if not found."""
    hid = hospital_id.upper()
    hospital = fetch_hospital_by_id(hid)
    if not hospital:
        return None, "live"
    return _ensure_risk(hospital), "live"
