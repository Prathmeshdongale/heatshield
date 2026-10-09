"""
mock_data.py — DEMO DATA only.
All values are synthetic and clearly labelled.
Replace calls to these functions with real service/repository calls
once the database and ML model are connected.

*** NEVER present this data as real hospital information. ***
"""

from datetime import date, datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Hospitals
# ---------------------------------------------------------------------------
HOSPITALS = {
    "H001": {
        "hospital_id": "H001",
        "name": "City General Hospital [DEMO]",
        "region": "Greater London",
        "address": "1 Demo Road, London, E1 1AA",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "contact_email": "ops@demo-citygen.nhs",
        "capacity_total": 300,
        "capacity_available": 72,
        "occupancy_pct": 76.0,
        "risk_status": "amber",
    },
    "H002": {
        "hospital_id": "H002",
        "name": "Riverside Medical Centre [DEMO]",
        "region": "Greater London",
        "address": "22 River Lane, London, SE1 0BB",
        "latitude": 51.4995,
        "longitude": -0.1157,
        "contact_email": "ops@demo-riverside.nhs",
        "capacity_total": 180,
        "capacity_available": 15,
        "occupancy_pct": 91.7,
        "risk_status": "red",
    },
    "H003": {
        "hospital_id": "H003",
        "name": "Northern District Hospital [DEMO]",
        "region": "Greater Manchester",
        "address": "5 North Street, Manchester, M1 2CC",
        "latitude": 53.4808,
        "longitude": -2.2426,
        "contact_email": "ops@demo-northern.nhs",
        "capacity_total": 250,
        "capacity_available": 120,
        "occupancy_pct": 52.0,
        "risk_status": "green",
    },
}

# Risk thresholds used by forecasts and alerts
RISK_THRESHOLDS = {"green": 70.0, "amber": 85.0, "red": 100.0}


def _risk_from_pct(pct: float) -> str:
    if pct >= 100:
        return "critical"
    if pct >= 85:
        return "red"
    if pct >= 70:
        return "amber"
    return "green"


# ---------------------------------------------------------------------------
# Forecasts
# ---------------------------------------------------------------------------
def get_demo_forecast(hospital_id: str, days: int) -> dict:
    hospital = HOSPITALS.get(hospital_id)
    base_admissions = (hospital["capacity_total"] * hospital["occupancy_pct"] / 100) * 0.05
    today = date.today()
    points = []
    for i in range(1, days + 1):
        predicted = round(base_admissions + (i * 0.8), 1)
        lower = round(predicted * 0.85, 1)
        upper = round(predicted * 1.15, 1)
        proj_occ = min(hospital["occupancy_pct"] + i * 1.2, 105)
        points.append({
            "forecast_date": str(today + timedelta(days=i)),
            "predicted_admissions": predicted,
            "confidence_lower": lower,
            "confidence_upper": upper,
            "risk_status": _risk_from_pct(proj_occ),
        })
    return {
        "hospital_id": hospital_id,
        "model_version": "v1.2.0-demo",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days_requested": days,
        "points": points,
    }


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------
def get_demo_weather(hospital_id: str, days: int) -> dict:
    today = date.today()
    base_temps = [34.2, 33.8, 36.1, 37.4, 35.9, 32.0, 30.5]
    observations = []
    for i in range(days):
        t_max = base_temps[i % len(base_temps)]
        observations.append({
            "observation_date": str(today - timedelta(days=days - 1 - i)),
            "temperature_max_c": t_max,
            "temperature_min_c": round(t_max - 10.5, 1),
            "humidity_pct": 65.0 + (i % 3) * 3,
            "heat_index_c": round(t_max + 3.8, 1),
            "condition": "Heatwave" if t_max > 35 else "Hot",
        })
    return {
        "hospital_id": hospital_id,
        "days_requested": days,
        "observations": observations,
    }


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
def get_demo_alerts(hospital_id: str | None) -> list[dict]:
    all_alerts = [
        {
            "alert_id": "ALT-0041",
            "hospital_id": "H001",
            "hospital_name": "City General Hospital [DEMO]",
            "severity": "medium",
            "message": "DEMO: Predicted admissions will exceed 80% capacity on 2026-10-13",
            "triggered_at": datetime(2026, 10, 9, 6, 0, 0, tzinfo=timezone.utc),
            "forecast_date": "2026-10-13",
            "resolved": False,
        },
        {
            "alert_id": "ALT-0042",
            "hospital_id": "H002",
            "hospital_name": "Riverside Medical Centre [DEMO]",
            "severity": "high",
            "message": "DEMO: Predicted admissions exceed 85% capacity on 2026-10-12",
            "triggered_at": datetime(2026, 10, 9, 6, 5, 0, tzinfo=timezone.utc),
            "forecast_date": "2026-10-12",
            "resolved": False,
        },
    ]
    if hospital_id:
        return [a for a in all_alerts if a["hospital_id"] == hospital_id]
    return all_alerts


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
DEMO_METRICS = {
    "model_version": "v1.2.0-demo",
    "evaluated_on": "2026-10-01",
    "mae": 3.8,
    "rmse": 5.1,
    "r2": 0.87,
    "training_data_from": "2023-01-01",
    "training_data_to": "2026-09-30",
    "feature_count": 12,
}
