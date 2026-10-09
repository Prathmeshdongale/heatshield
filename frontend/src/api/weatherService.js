/**
 * weatherService.js
 *
 * Endpoints consumed (from docs/api-contract.md):
 *   GET /weather/current
 *   GET /weather/history?days=N
 *
 * Response shapes (agreed contract):
 *   current : { timestamp, temp_c, humidity_pct, heat_index, source }
 *   history : [ { timestamp, temp_c, humidity_pct, heat_index, source }, … ]
 *
 * Demo fallback data is sourced exclusively from src/data/ modules.
 * No Supabase keys or secrets are referenced here.
 */

import { callApi, withDemoFallback } from './serviceHelpers.js';
import {
  DEMO_WEATHER_CURRENT_FULL as DEMO_CURRENT,
  DEMO_HEATWAVE_SERIES      as DEMO_HISTORY,
} from '../data/demoPages.js';

// ── Mappers ──────────────────────────────────────────────────────────────────
// The backend may return snake_case keys; ensure the UI always gets a
// consistent shape even if the backend adds extra fields.

function mapCurrentWeather(raw) {
  return {
    timestamp:    raw.timestamp,
    temp_c:       raw.temp_c,
    humidity_pct: raw.humidity_pct,
    heat_index:   raw.heat_index,
    source:       raw.source ?? 'api',
  };
}

function mapWeatherHistory(rawArray) {
  return rawArray.map((row) => ({
    date:         row.date ?? row.timestamp?.slice(0, 10),
    temp_c:       row.temp_c,
    heat_index:   row.heat_index,
    humidity_pct: row.humidity_pct,
    source:       row.source ?? 'api',
  }));
}

// ── Service functions ─────────────────────────────────────────────────────────

/**
 * fetchCurrentWeather — GET /weather/current
 * Returns current weather conditions.
 */
export async function fetchCurrentWeather() {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/weather/current').then((r) => mapCurrentWeather(r.data))
    ),
    () => ({ ...DEMO_CURRENT, source: 'DEMO — synthetic data' })
  );
}

/**
 * fetchWeatherHistory — GET /weather/history?days=N
 *
 * @param {number} days  — number of history days to fetch (default 7)
 */
export async function fetchWeatherHistory(days = 7) {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/weather/history', { params: { days } }).then((r) => mapWeatherHistory(r.data))
    ),
    () => DEMO_HISTORY.slice(-days).map((row) => ({ ...row, source: 'DEMO — synthetic data' }))
  );
}
