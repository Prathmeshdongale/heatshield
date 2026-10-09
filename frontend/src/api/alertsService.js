/**
 * alertsService.js — fetches alerts and health data directly from the API. No demo fallback.
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

function mapAlert(raw) {
  return {
    id:        raw.alert_id,
    severity:  raw.severity,
    message:   raw.message,
    timestamp: raw.triggered_at,
    facility:  raw.hospital_name ?? 'System',
  };
}

export async function fetchAlerts(hospitalId = null) {
  return call((c) => {
    const params = hospitalId ? { hospital_id: hospitalId } : {};
    return c.get('/alerts', { params }).then((r) => (r.data?.data ?? []).map(mapAlert));
  });
}

export async function fetchHealth() {
  return call((c) => c.get('/health').then((r) => r.data));
}
