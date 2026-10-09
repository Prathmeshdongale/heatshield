"""
risk.py — canonical risk-status calculation.

Risk is derived solely from projected occupancy:
  projected_occupancy_pct = (predicted_admissions / capacity_total) * 100

Thresholds (agreed with frontend and ML team — do not change unilaterally):
  < 70 %   → green
  70–84 %  → amber
  85–99 %  → red
  ≥ 100 %  → critical

If capacity_total is unavailable or zero, returns "unknown" so the caller
can surface that to the frontend rather than returning a misleading value.

These thresholds are the ONLY place risk_status should be computed.
All services must import calculate_risk() from here.
"""

_THRESHOLDS = [
    (100.0, "critical"),
    (85.0,  "red"),
    (70.0,  "amber"),
    (0.0,   "green"),
]


def calculate_risk(predicted_admissions: float, capacity_total: int | None) -> str:
    """
    Return a risk_status string based on projected occupancy.

    Args:
        predicted_admissions: ML-predicted daily admissions (float ≥ 0).
        capacity_total:       Total bed capacity for the hospital (int > 0).
                              Pass None if unavailable.

    Returns:
        One of: "green" | "amber" | "red" | "critical" | "unknown"
    """
    if capacity_total is None or capacity_total <= 0:
        return "unknown"
    if predicted_admissions < 0:
        return "unknown"

    projected_pct = (predicted_admissions / capacity_total) * 100

    for threshold, label in _THRESHOLDS:
        if projected_pct >= threshold:
            return label

    return "green"  # unreachable but satisfies type checker


def calculate_risk_from_pct(occupancy_pct: float | None) -> str:
    """
    Convenience overload for when occupancy_pct is already computed.
    Used by capacity_service when only snapshot data is available.
    """
    if occupancy_pct is None or occupancy_pct < 0:
        return "unknown"
    for threshold, label in _THRESHOLDS:
        if occupancy_pct >= threshold:
            return label
    return "green"
