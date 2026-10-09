/**
 * forecastService.js — fetches forecast data directly from the API. No demo fallback.
 */

import apiClient, { ApiError } from './client.js';

async function call(fn) {
  try {
    const res = await fn(apiClient);
    return { data: res, error: null, isDemo: false, source: 'api' };
  } catch (err) {
    const e = err instanceof ApiError ? err : new ApiError({ message: String(err), raw: err });
    return { data: null, error: e, isDemo: false, source: 'api' };
  }
}

function mapForecastRow(row) {
  return {
    date:                 row.forecast_date,
    predicted_admissions: row.predicted_admissions,
    upper_ci:             row.confidence_upper ?? null,
    lower_ci:             row.confidence_lower ?? null,
    risk_status:          row.risk_status,
    type:                 'forecast',
    source: 'api',
  };
}

export async function fetchDemandForecast(days = 7, hospitalId = 'H001') {
  return call((c) =>
    c.get('/forecasts', { params: { hospital_id: hospitalId, days } })
     .then((r) => (r.data?.data?.points ?? []).map(mapForecastRow))
  );
}

/**
 * fetchCombinedDemandSeries — returns forecast-only series (no historical endpoint exists).
 */
export async function fetchCombinedDemandSeries(historyDays = 14, forecastDays = 7, hospitalId = 'H001') {
  const result = await fetchDemandForecast(forecastDays, hospitalId);
  return result;
}

/**
 * fetchHistoricalDemand — no backend endpoint. Returns empty array.
 */
export async function fetchHistoricalDemand() {
  return { data: [], error: null, isDemo: false, source: 'api' };
}
