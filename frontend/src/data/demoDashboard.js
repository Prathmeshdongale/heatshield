/**
 * demoDashboard.js
 *
 * ⚠️  SYNTHETIC DEMO DATA — NOT REAL PREDICTIONS OR CLINICAL DATA ⚠️
 *
 * All values in this file are randomly generated for UI development purposes
 * only. They do not represent actual hospital capacity, real forecasts, or
 * genuine weather observations. Do not use these figures for any operational,
 * medical, or planning decisions.
 *
 * This module is the single source of truth for dashboard demo data so that
 * components stay free of hardcoded values and the data origin is transparent.
 */

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isoDate(offsetDays) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

function rand(min, max) {
  return Math.round(min + Math.random() * (max - min));
}

// ---------------------------------------------------------------------------
// Summary KPIs
// ---------------------------------------------------------------------------

export const DEMO_SUMMARY = {
  forecastPeakAdmissions: 127,        // highest predicted single-day admissions next 7 days
  forecastPeakDate: isoDate(3),        // date of that peak
  avgHospitalOccupancy: 74,            // % average across all facilities
  facilitiesAtHighRisk: 2,             // count of high/critical facilities
  overallRiskLevel: 'high',           // low | medium | high | critical
  dataFreshnessMinutes: 18,            // minutes since last data refresh
  source: 'DEMO — synthetic data',
};

// ---------------------------------------------------------------------------
// 14-day demand history + 7-day forecast (merged for the chart)
// ---------------------------------------------------------------------------

export const DEMO_DEMAND_SERIES = [
  // --- 14 days history ---
  ...Array.from({ length: 14 }, (_, i) => {
    const admissions = rand(75, 115);
    return {
      date: isoDate(i - 14),
      admissions,
      er_visits: rand(140, 200),
      predicted_admissions: null,
      upper_ci: null,
      lower_ci: null,
      type: 'historical',
    };
  }),
  // --- 7 days forecast ---
  ...Array.from({ length: 7 }, (_, i) => {
    const predicted = rand(85, 135);
    return {
      date: isoDate(i + 1),
      admissions: null,
      er_visits: null,
      predicted_admissions: predicted,
      upper_ci: predicted + rand(8, 18),
      lower_ci: predicted - rand(6, 14),
      type: 'forecast',
    };
  }),
];

// ---------------------------------------------------------------------------
// 7-day weather trend
// ---------------------------------------------------------------------------

export const DEMO_WEATHER_SERIES = Array.from({ length: 7 }, (_, i) => ({
  date: isoDate(i - 6),
  temp_c: rand(28, 41),
  heat_index: rand(32, 52),
  humidity_pct: rand(55, 85),
  source: 'DEMO',
}));

// Current conditions (most recent reading)
export const DEMO_WEATHER_CURRENT = {
  temp_c: DEMO_WEATHER_SERIES[DEMO_WEATHER_SERIES.length - 1].temp_c,
  heat_index: DEMO_WEATHER_SERIES[DEMO_WEATHER_SERIES.length - 1].heat_index,
  humidity_pct: DEMO_WEATHER_SERIES[DEMO_WEATHER_SERIES.length - 1].humidity_pct,
  timestamp: new Date().toISOString(),
  source: 'DEMO — synthetic data',
};

// ---------------------------------------------------------------------------
// Hospital capacity / risk rows
// ---------------------------------------------------------------------------

export const DEMO_HOSPITALS = [
  {
    hospital_id: 'H001',
    name: 'City General Hospital',
    region: 'North',
    total_beds: 400,
    icu_beds: 40,
    occupancy_pct: 88,
    icu_occupancy_pct: 92,
    risk_level: 'critical',
    predicted_surge: 18,
    source: 'DEMO',
  },
  {
    hospital_id: 'H002',
    name: 'Eastside Medical Centre',
    region: 'East',
    total_beds: 280,
    icu_beds: 28,
    occupancy_pct: 76,
    icu_occupancy_pct: 71,
    risk_level: 'high',
    predicted_surge: 12,
    source: 'DEMO',
  },
  {
    hospital_id: 'H003',
    name: 'Westpark Hospital',
    region: 'West',
    total_beds: 320,
    icu_beds: 32,
    occupancy_pct: 61,
    icu_occupancy_pct: 55,
    risk_level: 'medium',
    predicted_surge: 7,
    source: 'DEMO',
  },
  {
    hospital_id: 'H004',
    name: 'Southfield Clinic',
    region: 'South',
    total_beds: 180,
    icu_beds: 20,
    occupancy_pct: 45,
    icu_occupancy_pct: 40,
    risk_level: 'low',
    predicted_surge: 3,
    source: 'DEMO',
  },
];

// ---------------------------------------------------------------------------
// Recent alerts
// ---------------------------------------------------------------------------

export const DEMO_ALERTS = [
  {
    id: 'A001',
    severity: 'critical',
    message: 'City General Hospital ICU occupancy exceeded 90% threshold.',
    timestamp: new Date(Date.now() - 12 * 60 * 1000).toISOString(),   // 12 min ago
    facility: 'City General Hospital',
  },
  {
    id: 'A002',
    severity: 'high',
    message: 'Forecast model predicts surge of 18+ admissions at City General in 3 days.',
    timestamp: new Date(Date.now() - 34 * 60 * 1000).toISOString(),   // 34 min ago
    facility: 'City General Hospital',
  },
  {
    id: 'A003',
    severity: 'high',
    message: 'Heat index reached 47 °C — elevated demand risk for next 48 hours.',
    timestamp: new Date(Date.now() - 58 * 60 * 1000).toISOString(),   // 58 min ago
    facility: 'System-wide',
  },
  {
    id: 'A004',
    severity: 'medium',
    message: 'Eastside Medical Centre general ward occupancy above 75%.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 h ago
    facility: 'Eastside Medical Centre',
  },
  {
    id: 'A005',
    severity: 'low',
    message: 'Scheduled model retrain completed. Metrics updated.',
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5 h ago
    facility: 'System',
  },
];
