/**
 * weatherService.js — fetches weather data directly from the API. No demo fallback.
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

function mapCurrentWeather(observations) {
  const latest = observations[observations.length - 1] ?? {};
  return {
    timestamp:    latest.observation_date,
    temp_c:       latest.temperature_max_c,
    humidity_pct: latest.humidity_pct,
    heat_index:   latest.heat_index_c,
    source: 'api',
  };
}

function mapHistory(observations) {
  return observations.map((r) => ({
    date:         r.observation_date,
    temp_c:       r.temperature_max_c,
    heat_index:   r.heat_index_c,
    humidity_pct: r.humidity_pct,
    source: 'api',
  }));
}

export async function fetchCurrentWeather(hospitalId = 'H001') {
  return call((c) =>
    c.get('/weather', { params: { hospital_id: hospitalId, days: 1 } })
     .then((r) => mapCurrentWeather(r.data?.data?.observations ?? []))
  );
}

export async function fetchWeatherHistory(days = 7, hospitalId = 'H001') {
  return call((c) =>
    c.get('/weather', { params: { hospital_id: hospitalId, days } })
     .then((r) => mapHistory(r.data?.data?.observations ?? []))
  );
}
