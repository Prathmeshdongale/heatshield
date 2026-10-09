/**
 * hospitalService.js — fetches hospital data directly from the API.
 * No demo fallback. Returns { data, error, source } where source is always 'api'.
 */

import apiClient, { ApiError } from './client.js';

const RISK_MAP = {
  green: 'low', amber: 'medium', red: 'high', critical: 'critical',
  low: 'low', medium: 'medium', high: 'high',
};
function normaliseRisk(raw) { return RISK_MAP[raw] ?? 'unknown'; }

function mapHospital(raw) {
  return {
    hospital_id:       raw.hospital_id,
    name:              raw.name,
    region:            raw.region,
    total_beds:        raw.capacity_total,
    capacity_available: raw.capacity_available,
    icu_beds:          raw.icu_beds ?? null,
    occupancy_pct:     raw.occupancy_pct,
    icu_occupancy_pct: raw.icu_occupancy_pct ?? null,
    ed_occupancy_pct:  raw.ed_occupancy_pct ?? null,
    risk_level:        normaliseRisk(raw.risk_status),
    risk_status:       raw.risk_status,
    predicted_surge:   raw.predicted_surge ?? null,
    source: 'api',
  };
}

function mapHospitalRisk(raw) {
  return {
    hospital_id:    raw.hospital_id,
    date:           raw.updated_at?.slice(0, 10) ?? new Date().toISOString().slice(0, 10),
    occupancy_pct:  raw.occupancy_pct,
    risk_level:     normaliseRisk(raw.risk_status),
    predicted_surge: raw.predicted_surge ?? null,
    source: 'api',
  };
}

async function call(fn) {
  try {
    const res = await fn(apiClient);
    return { data: res, error: null, isDemo: false, source: 'api' };
  } catch (err) {
    const e = err instanceof ApiError ? err : new ApiError({ message: String(err), raw: err });
    return { data: null, error: e, isDemo: false, source: 'api' };
  }
}

export async function fetchHospitals() {
  return call((c) => c.get('/hospitals').then((r) => (r.data?.data ?? []).map(mapHospital)));
}

export async function fetchHospitalRisk(hospitalId) {
  return call((c) =>
    c.get(`/hospitals/${hospitalId}`).then((r) => mapHospitalRisk(r.data?.data ?? {}))
  );
}

export async function fetchAllHospitalsWithRisk() {
  const listResult = await fetchHospitals();
  if (listResult.error || !listResult.data?.length) return listResult;

  const riskResults = await Promise.all(
    listResult.data.map((h) => fetchHospitalRisk(h.hospital_id))
  );

  const merged = listResult.data.map((h, i) => ({
    ...h,
    ...(riskResults[i]?.data ?? {}),
  }));

  const firstErr = listResult.error ?? riskResults.find((r) => r.error)?.error ?? null;
  return { data: merged, error: firstErr, isDemo: false, source: 'api' };
}
