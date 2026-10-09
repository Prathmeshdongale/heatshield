/**
 * forecastService.js
 *
 * Endpoints consumed (from docs/api-contract.md):
 *   GET /demand/historical?days=N
 *   GET /demand/forecast?days=N
 *
 * Response shapes (agreed contract):
 *   historical : [ { date, admissions, er_visits, source }, … ]
 *   forecast   : [ { date, predicted_admissions, lower_ci, upper_ci,
 *                    confidence, source }, … ]
 *
 * This service merges history + forecast into the combined series format
 * expected by DemandChart (type: 'historical' | 'forecast').
 */

import { callApi, withDemoFallback } from './serviceHelpers.js';
import { makeForecastSeries }        from '../data/demoPages.js';

// ── Mappers ──────────────────────────────────────────────────────────────────

function mapHistoricalRow(row) {
  return {
    date:                 row.date,
    admissions:           row.admissions,
    er_visits:            row.er_visits,
    predicted_admissions: null,
    upper_ci:             null,
    lower_ci:             null,
    type:                 'historical',
    source:               row.source ?? 'api',
  };
}

function mapForecastRow(row) {
  return {
    date:                 row.date,
    admissions:           null,
    er_visits:            null,
    predicted_admissions: row.predicted_admissions,
    upper_ci:             row.upper_ci ?? null,
    lower_ci:             row.lower_ci ?? null,
    confidence:           row.confidence ?? null,
    type:                 'forecast',
    source:               row.source ?? 'api',
  };
}

// ── Service functions ─────────────────────────────────────────────────────────

/**
 * fetchHistoricalDemand — GET /demand/historical?days=N
 *
 * @param {number} days  — history window (default 14)
 */
export async function fetchHistoricalDemand(days = 14) {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/demand/historical', { params: { days } })
        .then((r) => r.data.map(mapHistoricalRow))
    ),
    () => makeForecastSeries('all', 7)
        .filter((r) => r.type === 'historical')
        .slice(-days)
        .map((r) => ({ ...r, source: 'DEMO — synthetic data' }))
  );
}

/**
 * fetchDemandForecast — GET /demand/forecast?days=N
 *
 * @param {number} days  — forecast horizon (default 7)
 */
export async function fetchDemandForecast(days = 7) {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/demand/forecast', { params: { days } })
        .then((r) => r.data.map(mapForecastRow))
    ),
    () => makeForecastSeries('all', days)
        .filter((r) => r.type === 'forecast')
        .map((r) => ({ ...r, source: 'DEMO — synthetic data' }))
  );
}

/**
 * fetchCombinedDemandSeries — fetches history + forecast and merges them
 * into a single chronological array suitable for DemandChart.
 *
 * @param {number} historyDays  — default 14
 * @param {number} forecastDays — default 7
 */
export async function fetchCombinedDemandSeries(historyDays = 14, forecastDays = 7) {
  const [histResult, forecastResult] = await Promise.all([
    fetchHistoricalDemand(historyDays),
    fetchDemandForecast(forecastDays),
  ]);

  const merged = [
    ...(histResult.data ?? []),
    ...(forecastResult.data ?? []),
  ];

  // Both failed → isDemo true; either succeeded from API → isDemo false
  const isDemo  = histResult.isDemo && forecastResult.isDemo;
  const error   = histResult.error ?? forecastResult.error ?? null;
  const source  = isDemo ? 'demo' : 'api';

  return { data: merged, isDemo, error, source };
}
