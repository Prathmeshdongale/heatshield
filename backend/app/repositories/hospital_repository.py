"""
hospital_repository.py — Supabase queries for hospitals and capacity.
No demo fallback — returns real DB data or raises on failure.
"""

import logging
from app.integrations.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def fetch_all_hospitals() -> list[dict]:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client not configured")

    hospitals_raw = client.select(
        "hospitals",
        columns="hospital_id,name,region,address,latitude,longitude,capacity_total,data_status",
    )
    hospitals = {h["hospital_id"]: h for h in hospitals_raw}

    # Set defaults in case no capacity snapshot exists yet
    for h in hospitals.values():
        h.setdefault("capacity_available", 0)
        h.setdefault("occupancy_pct", 0.0)
        h.setdefault("risk_status", "green")

    # Merge latest capacity snapshot per hospital
    capacity_raw = client.select(
        "hospital_capacity",
        columns="hospital_id,recorded_date,capacity_total,capacity_available,occupancy_pct,risk_status",
        order="recorded_date",
        desc=True,
    )
    seen: set[str] = set()
    for row in capacity_raw:
        hid = row["hospital_id"]
        if hid not in seen and hid in hospitals:
            hospitals[hid].update(row)
            seen.add(hid)

    return list(hospitals.values())


def fetch_hospital_by_id(hospital_id: str) -> dict | None:
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client not configured")

    hid = hospital_id.upper()
    hospital = client.select("hospitals", filters={"hospital_id": hid}, single=True)
    if not hospital:
        return None

    hospital.setdefault("capacity_available", 0)
    hospital.setdefault("occupancy_pct", 0.0)
    hospital.setdefault("risk_status", "green")

    cap_rows = client.select(
        "hospital_capacity",
        columns="recorded_date,capacity_total,capacity_available,occupancy_pct,risk_status",
        filters={"hospital_id": hid},
        order="recorded_date",
        desc=True,
        limit=1,
    )
    if cap_rows:
        hospital.update(cap_rows[0])

    return hospital
