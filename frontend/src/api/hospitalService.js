/**
 * hospitalService.js
 *
 * Endpoints consumed (from docs/api-contract.md):
 *   GET /hospitals
 *   GET /hospitals/{id}/risk
 *
 * Response shapes (agreed contract):
 *   hospitals : [ { id, name, region, total_beds, icu_beds }, … ]
 *   risk      : { hospital_id, date, occupancy_pct, risk_level,
 *                 predicted_surge, source }
 *
 * Note on field naming: the backend uses "id" on the /hospitals list,
 * but "hospital_id" on the risk endpoint. The mapper normalises both
 * to hospital_id for consistency across the UI.
 */

import { callApi, withDemoFallback } from './serviceHelpers.js';
import {
  DEMO_HOSPITAL_LIST_SUMMARY,
  DEMO_HOSPITAL_DETAILS,
} from '../data/demoPages.js';

// ── Mappers ──────────────────────────────────────────────────────────────────

function mapHospital(raw) {
  return {
    hospital_id:  raw.hospital_id ?? raw.id,
    name:         raw.name,
    region:       raw.region,
    total_beds:   raw.total_beds,
    icu_beds:     raw.icu_beds,
    source:       raw.source ?? 'api',
  };
}

function mapHospitalRisk(raw) {
  return {
    hospital_id:   raw.hospital_id,
    date:          raw.date,
    occupancy_pct: raw.occupancy_pct,
    risk_level:    raw.risk_level,
    predicted_surge: raw.predicted_surge,
    source:        raw.source ?? 'api',
  };
}

// ── Service functions ─────────────────────────────────────────────────────────

/**
 * fetchHospitals — GET /hospitals
 * Returns list of all registered hospitals.
 */
export async function fetchHospitals() {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/hospitals').then((r) => r.data.map(mapHospital))
    ),
    () => DEMO_HOSPITAL_LIST_SUMMARY.map((h) => ({ ...h, source: 'DEMO — synthetic data' }))
  );
}

/**
 * fetchHospitalRisk — GET /hospitals/{id}/risk
 * Returns capacity risk data for one hospital.
 *
 * @param {string} hospitalId
 */
export async function fetchHospitalRisk(hospitalId) {
  return withDemoFallback(
    () => callApi((client) =>
      client.get(`/hospitals/${hospitalId}/risk`).then((r) => mapHospitalRisk(r.data))
    ),
    () => {
      const detail = DEMO_HOSPITAL_DETAILS[hospitalId];
      if (!detail) return null;
      return {
        hospital_id:    detail.hospital_id,
        date:           new Date().toISOString().slice(0, 10),
        occupancy_pct:  detail.occupancy_pct,
        risk_level:     detail.risk_level,
        predicted_surge: detail.predicted_surge,
        source:         'DEMO — synthetic data',
      };
    }
  );
}

/**
 * fetchAllHospitalsWithRisk — fetches the hospital list then fetches risk
 * for each one in parallel and merges the results.
 * Returns merged rows ready for RiskTable.
 */
export async function fetchAllHospitalsWithRisk() {
  const listResult = await fetchHospitals();
  if (!listResult.data?.length) {
    return { data: [], isDemo: listResult.isDemo, error: listResult.error, source: listResult.source };
  }

  const riskResults = await Promise.all(
    listResult.data.map((h) => fetchHospitalRisk(h.hospital_id))
  );

  const merged = listResult.data.map((h, i) => ({
    ...h,
    ...(riskResults[i]?.data ?? {}),
  }));

  const anyIsDemo = listResult.isDemo || riskResults.some((r) => r.isDemo);
  const firstErr  = listResult.error ?? riskResults.find((r) => r.error)?.error ?? null;

  return {
    data:   merged,
    isDemo: anyIsDemo,
    error:  firstErr,
    source: anyIsDemo ? 'demo' : 'api',
  };
}
