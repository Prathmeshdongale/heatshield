"""
Synthetic dataset for HC-02: Predicting Hospital Demand During Extreme Heat (NHS England style).

Grain: one row per hospital trust per day.
Calibrated to NHS England A&E patterns (national ~2,000-2,700 attendances/day per large
acute trust is NOT assumed; trusts here range ~150-650/day for a single main department).
NOT real patient data. Trust names/codes are fictional. Replace/blend with the real NHS England
A&E monthly CSVs (England.nhs.uk statistics) for validation.

Run:  python generate_synthetic_nhs_heat_dataset.py
Out:  nhs_heat_hospital_demand_synthetic.csv
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
START, END = "2024-04-01", "2026-09-30"
dates = pd.date_range(START, END, freq="D")
n_days = len(dates)

# ---------------- Regions (NHS England 7 regions) ----------------
regions = {
    # name: (mean annual temp offset, summer amplitude, n_trusts)
    "London":                  (11.5, 8.5, 4),
    "South East":              (10.8, 8.2, 4),
    "South West":              (10.5, 7.0, 3),
    "East of England":         (10.5, 8.3, 3),
    "Midlands":                (10.0, 8.0, 4),
    "North West":              (9.5, 6.8, 3),
    "North East and Yorkshire":(9.0, 7.0, 4),
}

# ---------------- Regional weather ----------------
doy = dates.dayofyear.values
season = -np.cos(2 * np.pi * (doy - 15) / 365.25)  # coldest mid-Jan, warmest mid-Jul

# Shared national weather pattern + regional noise; plus injected heatwaves
nat_noise = np.zeros(n_days)
for i in range(1, n_days):
    nat_noise[i] = 0.75 * nat_noise[i - 1] + rng.normal(0, 1.6)

heatwaves = [  # (start, end, peak uplift in degC) - mimics hot summers 2025/2026
    ("2025-06-19", "2025-07-02", 9.0),
    ("2025-08-08", "2025-08-14", 7.0),
    ("2026-05-18", "2026-05-27", 8.0),
    ("2026-06-20", "2026-07-02", 12.0),
    ("2026-07-18", "2026-07-26", 8.5),
    ("2026-08-10", "2026-08-15", 6.5),
]
hw_uplift = np.zeros(n_days)
for s, e, peak in heatwaves:
    idx = np.where((dates >= s) & (dates <= e))[0]
    shape = np.sin(np.linspace(0.15, np.pi - 0.15, len(idx)))
    hw_uplift[idx] += peak * shape

region_weather = {}
for r, (base, amp, _) in regions.items():
    rn = np.zeros(n_days)
    for i in range(1, n_days):
        rn[i] = 0.6 * rn[i - 1] + rng.normal(0, 0.9)
    tmean = base + amp * season * 0.9 + nat_noise + rn
    summer_mask = ((doy > 130) & (doy < 260)).astype(float)
    tmax = tmean + 4.5 + hw_uplift * summer_mask + rng.normal(0, 0.8, n_days)
    tmin = tmean - 4.0 + 0.55 * hw_uplift * summer_mask + rng.normal(0, 0.8, n_days)
    tmax = np.maximum(tmax, tmin + 2)
    region_weather[r] = (tmax, tmin)

# ---------------- Trusts ----------------
trusts = []
suffix = ["General", "Royal Infirmary", "University Hospitals", "City", "District General", "Teaching"]
k = 0
for r, (_, _, n) in regions.items():
    for j in range(n):
        k += 1
        size = rng.choice(["small", "medium", "large"], p=[0.25, 0.45, 0.30])
        beds = {"small": rng.integers(350, 550), "medium": rng.integers(550, 900), "large": rng.integers(900, 1500)}[size]
        trusts.append(dict(
            trust_id=f"SYN{k:03d}",
            trust_name=f"{r.split(' ')[0]} {rng.choice(suffix)} NHS Trust {k:02d}",
            region=r,
            hospital_size=size,
            urban=int(rng.random() < 0.7),
            general_acute_beds=int(beds),
            icu_beds=int(max(12, beds * rng.uniform(0.03, 0.055))),
            ambulances_available=int(max(8, beds / 25 * rng.uniform(0.8, 1.2))),
            baseline_staff_per_shift=int(beds * rng.uniform(0.55, 0.75)),
            pct_pop_over_65=round(rng.uniform(13, 27), 1),
            pct_pop_under_5=round(rng.uniform(4.5, 6.8), 1),
            imd_deprivation_decile=int(rng.integers(1, 11)),   # 1 = most deprived
            green_space_pct=round(rng.uniform(5, 45), 1),
            ac_cooled_wards_pct=round(rng.uniform(10, 70), 1),
            catchment_pop=int(beds * rng.uniform(380, 520)),
        ))
trust_df = pd.DataFrame(trusts)

bank_holidays = pd.to_datetime([
    "2024-04-01", "2024-05-06", "2024-05-27", "2024-08-26", "2024-12-25", "2024-12-26",
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-05", "2025-05-26", "2025-08-25",
    "2025-12-25", "2025-12-26", "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-04",
    "2026-05-25", "2026-08-31"])

# ---------------- Generate rows ----------------
rows = []
dow_att = np.array([1.10, 1.02, 0.99, 0.98, 0.99, 0.95, 0.97])  # Mon..Sun
for _, t in trust_df.iterrows():
    tmax, tmin = region_weather[t.region]
    tmax = tmax + rng.normal(0, 0.5, n_days)
    tmin = tmin + rng.normal(0, 0.4, n_days)
    rh = np.clip(70 - 1.2 * (tmax - 15) + rng.normal(0, 8, n_days), 25, 98)
    # Simplified heat index (humidity-adjusted feels-like)
    heat_index = tmax + 0.045 * np.clip(rh - 40, 0, None) * np.clip(tmax - 20, 0, None) / 4
    uv = np.clip(5.5 * season + 1.2 + rng.normal(0, 0.7, n_days), 0, 11)
    pm25 = np.clip(9 + 0.35 * np.clip(tmax - 22, 0, None) * 2 + rng.normal(0, 3, n_days) + 3 * t.urban, 2, 80)
    ozone = np.clip(45 + 3.0 * np.clip(tmax - 20, 0, None) + rng.normal(0, 10, n_days), 10, 260)
    # Heat exposure thresholds: a trust-region specific "heat threshold" (hotter south)
    thr = {"London": 26, "South East": 26, "East of England": 26, "South West": 25,
           "Midlands": 25, "North West": 24, "North East and Yorkshire": 24}[t.region]
    hot_excess = np.clip(tmax - thr, 0, None)
    hot_excess_l1 = np.r_[0, hot_excess[:-1]]
    hot_excess_l2 = np.r_[0, 0, hot_excess[:-2]]
    hot_excess_l3 = np.r_[0, 0, 0, hot_excess[:-3]]
    warm_night = (tmin > 18).astype(int)
    # Heatwave flag: >= 3 consecutive days with tmax >= thr
    above = (tmax >= thr).astype(int)
    run = np.zeros(n_days, dtype=int)
    for i in range(n_days):
        run[i] = run[i - 1] + 1 if (above[i] and i > 0) else int(above[i])
    heatwave_flag = (run >= 3).astype(int)
    # UKHSA-style heat health alert (synthetic rule)
    alert = np.where(hot_excess >= 9, "Red",
             np.where((hot_excess >= 5) & (heatwave_flag == 1), "Amber",
              np.where(hot_excess >= 2, "Yellow", "Normal")))

    vuln = 1 + 0.012 * (t.pct_pop_over_65 - 18) + 0.01 * (5 - t.imd_deprivation_decile) / 5 * 3
    cooling = 1 - 0.0025 * t.ac_cooled_wards_pct
    urban_heat = 1 + 0.06 * t.urban - 0.0015 * t.green_space_pct

    base_att = t.catchment_pop * 0.00040  # ~ daily attendances
    winter = 1 + 0.05 * (-season)  # winter respiratory bump
    heat_att = 1 + 0.018 * hot_excess + 0.008 * hot_excess_l1 + 0.004 * hot_excess_l2 \
               + 0.012 * warm_night * (hot_excess > 0) + 0.00015 * np.clip(pm25 - 20, 0, None)
    heat_att = 1 + (heat_att - 1) * vuln * urban_heat * cooling * 1.5
    dow = dow_att[dates.dayofweek]
    bh = np.where(dates.isin(bank_holidays), 0.92, 1.0)
    trend = 1 + 0.035 * np.arange(n_days) / 365   # +3.5%/yr growth
    lam = base_att * winter * heat_att * dow * bh * trend
    attendances = rng.negative_binomial(40, 40 / (40 + lam))

    adm_rate = np.clip(0.27 + 0.0035 * hot_excess + rng.normal(0, 0.012, n_days), 0.2, 0.42)
    emergency_adm = rng.binomial(attendances, adm_rate)

    # Heat-related admissions (dehydration, heat exhaustion/stroke, AKI, cardio-respiratory, hyponatraemia)
    heat_rate = 0.0015 + 0.0090 * hot_excess + 0.0050 * hot_excess_l1 + 0.0030 * hot_excess_l2 \
                + 0.0015 * hot_excess_l3
    heat_rate = heat_rate * vuln * cooling * urban_heat
    heat_adm = rng.binomial(emergency_adm, np.clip(heat_rate, 0, 0.35))

    # ICU demand
    icu_lam = t.icu_beds * (0.70 + 0.004 * (emergency_adm / (base_att * 0.27) - 1) * 100 * 0.35) \
              + 0.28 * heat_adm
    icu_demand = np.maximum(rng.poisson(np.clip(icu_lam, 1, None)), 0)

    # Bed occupancy (general acute): baseline 88% + pressure from admissions & slow discharge in heat
    bed_pressure = (emergency_adm - base_att * 0.27) / (t.general_acute_beds * 0.12)
    occ_pct = np.clip(0.86 + 0.10 * bed_pressure + 0.011 * hot_excess
                      + rng.normal(0, 0.012, n_days) + 0.03 * (-season) * 0.4, 0.70, 1.12) * 100
    beds_occupied = np.round(occ_pct / 100 * t.general_acute_beds).astype(int)

    # Ambulance
    amb_callouts = rng.poisson(np.clip(t.ambulances_available * 9.5 * (1 + 0.025 * hot_excess + 0.012 * hot_excess_l1) * dow, 1, None))
    handover_delay_30 = np.clip(rng.normal(0.18 + 0.012 * hot_excess + 0.25 * np.clip(occ_pct / 100 - 0.92, 0, None), 0.04, n_days), 0, 0.95) * 100

    # Staffing
    heat_staff_absence = np.clip(rng.normal(4.2 + 0.18 * hot_excess + 0.35 * warm_night + 0.6 * (-season > 0.5), 0.6, n_days), 2, 20)
    staff_required = np.round(t.baseline_staff_per_shift * (attendances / (base_att * 1.05)) ** 0.5 * (1 + 0.02 * heat_adm / np.maximum(1, t.icu_beds) * 10)).astype(int)
    staff_available = np.round(t.baseline_staff_per_shift * 1.06 * (1 - heat_staff_absence / 100)).astype(int)
    staff_gap = staff_required - staff_available

    # Critical medicines / consumables (units per day)
    iv_fluids_litres = np.round(rng.normal(1, 0.06, n_days) * (emergency_adm * 1.8 + heat_adm * 6.5), 0).astype(int)
    oral_rehydration_sachets = np.round(rng.normal(1, 0.08, n_days) * (attendances * 0.35 + heat_adm * 18)).astype(int)
    insulin_units_needed = np.round(rng.normal(1, 0.05, n_days) * (emergency_adm * 0.9) * (1 + 0.004 * hot_excess)).astype(int)
    cooling_equipment_in_use = np.round(rng.normal(1, 0.1, n_days) * (heat_adm * 0.6 + icu_demand * 0.15)).astype(int)
    oxygen_cylinders_used = np.round(rng.normal(1, 0.07, n_days) * (icu_demand * 3.0 + emergency_adm * 0.12)).astype(int)
    stock_days_remaining = np.clip(rng.normal(14 - 0.45 * hot_excess - 0.2 * heat_adm / np.maximum(1, t.icu_beds), 1.2, n_days), 1, 30)

    capacity_exceeded = ((occ_pct > 100) | (icu_demand > t.icu_beds) | (staff_gap > 0.08 * staff_required)).astype(int)
    critical_incident = ((occ_pct > 103) & (icu_demand > 1.08 * t.icu_beds)).astype(int)

    df = pd.DataFrame(dict(
        date=dates, trust_id=t.trust_id, tmax_c=tmax.round(1), tmin_c=tmin.round(1),
        humidity_pct=rh.round(0), heat_index_c=heat_index.round(1), uv_index=uv.round(1),
        pm25_ugm3=pm25.round(1), ozone_ugm3=ozone.round(0), warm_night_flag=warm_night,
        consecutive_hot_days=run, heatwave_flag=heatwave_flag, heat_health_alert=alert,
        day_of_week=dates.dayofweek, is_bank_holiday=dates.isin(bank_holidays).astype(int),
        ae_attendances=attendances, emergency_admissions=emergency_adm,
        heat_related_admissions=heat_adm, icu_demand=icu_demand,
        general_beds_occupied=beds_occupied, bed_occupancy_pct=occ_pct.round(1),
        ambulance_callouts=amb_callouts, pct_handover_delay_over_30min=handover_delay_30.round(1),
        staff_absence_pct=heat_staff_absence.round(1), staff_required=staff_required,
        staff_available=staff_available, staff_gap=staff_gap,
        iv_fluids_litres=iv_fluids_litres, oral_rehydration_sachets=oral_rehydration_sachets,
        insulin_units_needed=insulin_units_needed, cooling_equipment_in_use=cooling_equipment_in_use,
        oxygen_cylinders_used=oxygen_cylinders_used, critical_medicine_stock_days=stock_days_remaining.round(1),
        capacity_exceeded=capacity_exceeded, critical_incident=critical_incident,
    ))
    rows.append(df)

full = pd.concat(rows, ignore_index=True).merge(trust_df, on="trust_id", how="left")
# put static columns after ids
static = [c for c in trust_df.columns if c != "trust_id"]
cols = ["date", "trust_id"] + static + [c for c in full.columns if c not in ["date", "trust_id"] + static]
full = full[cols]
full.to_csv("nhs_heat_hospital_demand_synthetic.csv", index=False)
trust_df.to_csv("trust_metadata_synthetic.csv", index=False)
print(full.shape)
print(full.groupby("heat_health_alert")[["ae_attendances", "heat_related_admissions", "bed_occupancy_pct", "capacity_exceeded"]].mean().round(2))
