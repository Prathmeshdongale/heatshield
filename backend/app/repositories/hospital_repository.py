"""
hospital_repository.py — Supabase queries for hospital and capacity data.

Pattern:
  1. Try to query Supabase via the anon client.
  2. If DB is unavailable (client is None), fall back to demo data from mock_data.py.
  3. All DB values are returned as plain dicts; Pydantic validation happens in the route layer.

Parameterisation: all query values pass through the Supabase client's
chained filter methods, which parameterise values internally — no raw SQL
string interpolation is used.
"""

import logging
from app.integrations.supabase_client import get_supabase
from app.mock_data import HOSPITALS

logger = logging.getLogger(__name__)


def fetch_all_hospitals() -> list[dict]:
    """
    Returns all hospitals joined with their most-recent capacity snapshot.
    Falls back to mock data if DB is unavailable.
    """
    client = get_supabase()
    if client is None:
        logger.debug("DB unavailable — returning demo hospitals")
        return list(HOSPITALS.values())

    try:
        # Fetch hospitals
        h_resp = (
            client.table("hospitals")
            .select("hospital_id, name, region, capacity_total, data_status")
            .execute()
        )
        hospitals = {h["hospital_id"]: h for h in h_resp.data}

        # Fetch latest capacity per hospital using a subquery workaround:
        # Supabase REST doesn't support window functions, so we fetch all and
        # deduplicate in Python (acceptable for small hospital sets).
        c_resp = (
            client.table("hospital_capacity")
            .select(
                "hospital_id, recorded_date, capacity_total, "
                "capacity_available, occupancy_pct, risk_status"
            )
            .order("recorded_date", desc=True)
            .execute()
        )

        # Keep only the most-recent row per hospital
        seen: set[str] = set()
        for row in c_resp.data:
            hid = row["hospital_id"]
            if hid not in seen and hid in hospitals:
                hospitals[hid].update(row)
                seen.add(hid)

        return list(hospitals.values())

    except Exception as exc:
        logger.error("fetch_all_hospitals DB error: %s — falling back to demo", exc)
        return list(HOSPITALS.values())


def fetch_hospital_by_id(hospital_id: str) -> dict | None:
    """
    Returns full detail for one hospital including latest capacity.
    Falls back to mock data if DB is unavailable.
    Returns None if the hospital_id is not found.
    """
    client = get_supabase()
    if client is None:
        return HOSPITALS.get(hospital_id.upper())

    try:
        # Parameterised equality filter — no string interpolation
        h_resp = (
            client.table("hospitals")
            .select("*")
            .eq("hospital_id", hospital_id.upper())
            .single()
            .execute()
        )
        hospital = h_resp.data
        if not hospital:
            return None

        c_resp = (
            client.table("hospital_capacity")
            .select(
                "recorded_date, capacity_total, capacity_available, "
                "occupancy_pct, risk_status"
            )
            .eq("hospital_id", hospital_id.upper())
            .order("recorded_date", desc=True)
            .limit(1)
            .execute()
        )
        if c_resp.data:
            hospital.update(c_resp.data[0])

        return hospital

    except Exception as exc:
        logger.error("fetch_hospital_by_id DB error (%s): %s — falling back to demo", hospital_id, exc)
        return HOSPITALS.get(hospital_id.upper())
