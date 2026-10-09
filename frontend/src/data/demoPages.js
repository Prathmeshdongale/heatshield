/**
 * demoPages.js
 *
 * ⚠️  SYNTHETIC DEMO DATA — NOT REAL PREDICTIONS OR CLINICAL DATA ⚠️
 *
 * All values are generated for UI development only.
 * They do not represent real forecasts, actual hospital records,
 * genuine weather measurements, or trained ML model outputs.
 * Do not use these figures for any operational or clinical purpose.
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

// Seeded deterministic rand so values don't flicker on re-renders
function seeded(seed, min, max) {
  const x = Math.sin(seed + 1) * 10000;
  const r = x - Math.floor(x);
  return Math.round(min + r * (max - min));
}

// ============================================================
// FORECASTS PAGE
// ============================================================

export const DEMO_HOSPITALS_LIST = [
  { id: 'all',  name: 'All Hospitals (System-wide)' },
  { id: 'H001', name: 'City General Hospital'       },
  { id: 'H002', name: 'Eastside Medical Centre'      },
  { id: 'H003', name: 'Westpark Hospital'            },
  { id: 'H004', name: 'Southfield Clinic'            },
];

/**
 * Generate a combined history + forecast series for a given hospital and horizon.
 * Values are seeded per hospital so each hospital shows different numbers.
 */
export function makeForecastSeries(hospitalId, horizonDays) {
  const seed = hospitalId === 'all' ? 0
             : hospitalId === 'H001' ? 10
             : hospitalId === 'H002' ? 20
             : hospitalId === 'H003' ? 30
             : 40;

  const baseAdmissions = seeded(seed, 70, 130);
  const historyDays    = 14;

  const history = Array.from({ length: historyDays }, (_, i) => {
    const s = seed + i;
    const admissions = seeded(s, baseAdmissions - 20, baseAdmissions + 20);
    return {
      date: isoDate(i - historyDays),
      admissions,
      er_visits: seeded(s + 100, admissions + 40, admissions + 80),
      predicted_admissions: null,
      upper_ci: null,
      lower_ci: null,
      type: 'historical',
    };
  });

  const forecast = Array.from({ length: horizonDays }, (_, i) => {
    const s = seed + i + 200;
    // CI widens the further into the future
    const predicted = seeded(s, baseAdmissions - 10, baseAdmissions + 30);
    const ciWidth   = 8 + i * 1.5;
    return {
      date: isoDate(i + 1),
      admissions: null,
      er_visits: null,
      predicted_admissions: predicted,
      upper_ci: Math.round(predicted + ciWidth),
      lower_ci: Math.max(0, Math.round(predicted - ciWidth * 0.8)),
      confidence: Math.max(0.60, 0.90 - i * 0.03),
      type: 'forecast',
    };
  });

  return [...history, ...forecast];
}

export function makeForecastSummary(series, horizonDays) {
  const forecastRows = series.filter((r) => r.type === 'forecast');
  const historyRows  = series.filter((r) => r.type === 'historical');
  const peakRow      = forecastRows.reduce(
    (best, r) => (r.predicted_admissions > best.predicted_admissions ? r : best),
    forecastRows[0] ?? {}
  );
  const avgHistorical = historyRows.length
    ? Math.round(historyRows.reduce((s, r) => s + r.admissions, 0) / historyRows.length)
    : null;
  const avgForecast = forecastRows.length
    ? Math.round(forecastRows.reduce((s, r) => s + r.predicted_admissions, 0) / forecastRows.length)
    : null;
  const avgConfidence = forecastRows.length
    ? Math.round(
        (forecastRows.reduce((s, r) => s + (r.confidence ?? 0), 0) / forecastRows.length) * 100
      )
    : null;

  return {
    horizonDays,
    peakDate: peakRow?.date ?? '—',
    peakAdmissions: peakRow?.predicted_admissions ?? '—',
    avgHistoricalAdmissions: avgHistorical,
    avgForecastAdmissions: avgForecast,
    avgConfidencePct: avgConfidence,
    source: 'DEMO — synthetic data',
  };
}

// ============================================================
// HOSPITAL MONITORING PAGE
// ============================================================

export const DEMO_HOSPITAL_DETAILS = {
  H001: {
    hospital_id: 'H001',
    name: 'City General Hospital',
    region: 'North',
    address: '1 Demo Street, North District',
    total_beds: 400,
    icu_beds: 40,
    ed_bays: 24,
    occupancy_pct: 88,
    icu_occupancy_pct: 92,
    ed_occupancy_pct: 81,
    risk_level: 'critical',
    predicted_surge: 18,
    staff_on_duty: 142,
    last_updated: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
    source: 'DEMO',
  },
  H002: {
    hospital_id: 'H002',
    name: 'Eastside Medical Centre',
    region: 'East',
    address: '200 Demo Ave, East District',
    total_beds: 280,
    icu_beds: 28,
    ed_bays: 16,
    occupancy_pct: 76,
    icu_occupancy_pct: 71,
    ed_occupancy_pct: 68,
    risk_level: 'high',
    predicted_surge: 12,
    staff_on_duty: 98,
    last_updated: new Date(Date.now() - 18 * 60 * 1000).toISOString(),
    source: 'DEMO',
  },
  H003: {
    hospital_id: 'H003',
    name: 'Westpark Hospital',
    region: 'West',
    address: '50 Demo Blvd, West District',
    total_beds: 320,
    icu_beds: 32,
    ed_bays: 18,
    occupancy_pct: 61,
    icu_occupancy_pct: 55,
    ed_occupancy_pct: 58,
    risk_level: 'medium',
    predicted_surge: 7,
    staff_on_duty: 110,
    last_updated: new Date(Date.now() - 22 * 60 * 1000).toISOString(),
    source: 'DEMO',
  },
  H004: {
    hospital_id: 'H004',
    name: 'Southfield Clinic',
    region: 'South',
    address: '88 Demo Rd, South District',
    total_beds: 180,
    icu_beds: 20,
    ed_bays: 10,
    occupancy_pct: 45,
    icu_occupancy_pct: 40,
    ed_occupancy_pct: 42,
    risk_level: 'low',
    predicted_surge: 3,
    staff_on_duty: 64,
    last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    source: 'DEMO',
  },
};

/** 24-hour occupancy trend for a hospital (used in the detail chart) */
export function makeOccupancyTrend(hospitalId) {
  const base = DEMO_HOSPITAL_DETAILS[hospitalId]?.occupancy_pct ?? 70;
  return Array.from({ length: 24 }, (_, i) => ({
    hour: `${String(i).padStart(2, '0')}:00`,
    general_pct: seeded(hospitalId.charCodeAt(1) + i, base - 15, base + 5),
    icu_pct: seeded(hospitalId.charCodeAt(1) + i + 50, base - 10, base + 8),
  }));
}

export const DEMO_HOSPITAL_LIST_SUMMARY = Object.values(DEMO_HOSPITAL_DETAILS);

// ============================================================
// HEATWAVE ANALYSIS PAGE
// ============================================================

/** 30-day combined weather + demand history */
export const DEMO_HEATWAVE_SERIES = Array.from({ length: 30 }, (_, i) => {
  const temp      = seeded(i,       28, 43);
  const heatIndex = seeded(i + 100, temp + 2, temp + 12);
  const admissions = Math.round(
    80 + (heatIndex - 30) * 1.8 + seeded(i + 200, -8, 8)
  );
  return {
    date: isoDate(i - 29),
    temp_c: temp,
    heat_index: heatIndex,
    humidity_pct: seeded(i + 300, 55, 88),
    admissions: Math.max(50, admissions),
    er_visits: Math.max(90, Math.round(admissions * 1.65 + seeded(i + 400, -10, 10))),
    source: 'DEMO',
  };
});

export const DEMO_WEATHER_CURRENT_FULL = {
  temp_c: 36,
  heat_index: 44,
  humidity_pct: 71,
  wind_kph: 12,
  uv_index: 9,
  visibility_km: 14,
  timestamp: new Date().toISOString(),
  source: 'DEMO — synthetic data',
};

/** Heat category classification thresholds — for reference table */
export const HEAT_CATEGORIES = [
  { label: 'Normal',         min: null, max: 31,  color: '#22c55e', description: 'No special precautions needed.'              },
  { label: 'Caution',        min: 32,   max: 40,  color: '#84cc16', description: 'Fatigue possible with prolonged exposure.'    },
  { label: 'Extreme Caution',min: 41,   max: 45,  color: '#f59e0b', description: 'Heat cramps and exhaustion possible.'         },
  { label: 'Danger',         min: 46,   max: 51,  color: '#ef4444', description: 'Heat exhaustion likely; heatstroke possible.'  },
  { label: 'Extreme Danger', min: 52,   max: null, color: '#7c3aed', description: 'Heatstroke highly likely with exposure.'       },
];

export function classifyHeatIndex(value) {
  if (value == null) return HEAT_CATEGORIES[0];
  return (
    HEAT_CATEGORIES.slice().reverse().find((c) => c.min != null && value >= c.min)
    ?? HEAT_CATEGORIES[0]
  );
}

// ============================================================
// MODEL METRICS PAGE
// ============================================================

export const DEMO_MODEL_METRICS = {
  model_name: 'GradientBoostingRegressor',
  version: '1.2.0-demo',
  trained_at: '2024-10-01T08:00:00Z',
  training_duration_s: 142,
  training_rows: 18500,
  feature_count: 22,
  // Performance metrics (demo — not real model output)
  mae: 7.4,
  rmse: 9.8,
  r2: 0.87,
  mape: 8.2,          // Mean Absolute Percentage Error
  // Baseline comparison
  baseline_mae: 14.2,
  baseline_rmse: 18.6,
  source: 'DEMO — not real model results',
};

export const DEMO_FEATURE_IMPORTANCE = [
  { feature: 'heat_index_lag1',    importance: 0.214 },
  { feature: 'temp_c_lag1',        importance: 0.187 },
  { feature: 'day_of_week',        importance: 0.143 },
  { feature: 'humidity_pct',       importance: 0.112 },
  { feature: 'admissions_lag7',    importance: 0.098 },
  { feature: 'er_visits_lag1',     importance: 0.087 },
  { feature: 'month',              importance: 0.071 },
  { feature: 'temp_c_rolling_7d',  importance: 0.048 },
  { feature: 'public_holiday_flag',importance: 0.040 },
];

export const DEMO_TRAINING_HISTORY = [
  { run_id: 'run-005', date: '2024-10-01', mae: 7.4,  rmse: 9.8,  r2: 0.87, status: 'current'  },
  { run_id: 'run-004', date: '2024-09-15', mae: 8.1,  rmse: 10.4, r2: 0.85, status: 'previous' },
  { run_id: 'run-003', date: '2024-09-01', mae: 8.9,  rmse: 11.2, r2: 0.83, status: 'previous' },
  { run_id: 'run-002', date: '2024-08-15', mae: 10.2, rmse: 13.1, r2: 0.79, status: 'previous' },
  { run_id: 'run-001', date: '2024-08-01', mae: 12.7, rmse: 16.0, r2: 0.73, status: 'previous' },
];

// ============================================================
// SETTINGS PAGE
// ============================================================

export const SETTINGS_DEFAULTS = {
  apiBaseUrl:        '',
  refreshIntervalMs: 300_000,  // 5 minutes
  temperatureUnit:   'celsius',
  dateFormat:        'YYYY-MM-DD',
  showDemoBadges:    true,
};

export const API_STATUS_DEMO = {
  backend:  { status: 'unavailable', note: 'No backend running — displaying demo data'    },
  database: { status: 'unavailable', note: 'Supabase not connected — using static fixtures' },
  ml:       { status: 'unavailable', note: 'ML pipeline offline — metrics are demo values'  },
};
