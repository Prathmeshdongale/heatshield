/**
 * alertsService.js
 *
 * The agreed API contract (docs/api-contract.md) does not define an alerts
 * endpoint. This service is a placeholder that:
 *   1. Tries GET /alerts if the backend team adds it in the future.
 *   2. Falls back to demo alerts in the meantime.
 *
 * When the backend team adds an alerts endpoint they should update
 * docs/api-contract.md first; this service will then be updated to match.
 *
 * Demo data: src/data/demoDashboard.js → DEMO_ALERTS
 */

import { callApi, withDemoFallback } from './serviceHelpers.js';
import { DEMO_ALERTS } from '../data/demoDashboard.js';

function mapAlert(raw) {
  return {
    id:        raw.id,
    severity:  raw.severity,
    message:   raw.message,
    timestamp: raw.timestamp,
    facility:  raw.facility ?? raw.hospital_name ?? 'System',
  };
}

/**
 * fetchAlerts — GET /alerts (not yet in contract; always returns demo).
 * Replace the demoFn below with real demo data once the endpoint is agreed.
 */
export async function fetchAlerts() {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/alerts').then((r) => r.data.map(mapAlert))
    ),
    () => DEMO_ALERTS.map((a) => ({ ...a, source: 'DEMO — synthetic data' }))
  );
}

/**
 * fetchHealth — GET /health
 * Used by Settings page to show backend connectivity status.
 */
export async function fetchHealth() {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/health').then((r) => r.data)
    ),
    () => ({ status: 'demo', version: '0.0.0', source: 'DEMO' })
  );
}
