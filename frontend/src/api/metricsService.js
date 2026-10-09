/**
 * metricsService.js
 *
 * Endpoints consumed (from docs/api-contract.md):
 *   GET /metrics/model
 *
 * Response shape (agreed contract):
 *   { model_name, trained_at, mae, rmse, r2, source }
 *
 * Note: The backend schema does not include mape, baseline_mae,
 * baseline_rmse, feature_count, training_rows, training_duration_s,
 * feature_importance or training_history. Those fields are UI-layer
 * additions backed by demo data until the ML team extends the contract.
 * The service marks them as isDemo=true independently.
 */

import { callApi, withDemoFallback } from './serviceHelpers.js';
import {
  DEMO_MODEL_METRICS,
  DEMO_FEATURE_IMPORTANCE,
  DEMO_TRAINING_HISTORY,
} from '../data/demoPages.js';

// ── Mapper ───────────────────────────────────────────────────────────────────

function mapModelMetrics(raw) {
  return {
    model_name: raw.model_name,
    trained_at: raw.trained_at,
    mae:        raw.mae,
    rmse:       raw.rmse,
    r2:         raw.r2,
    source:     raw.source ?? 'api',
    // Fields not yet in the API contract — flagged explicitly
    mape:               null,
    baseline_mae:       null,
    baseline_rmse:      null,
    feature_count:      null,
    training_rows:      null,
    training_duration_s:null,
    version:            null,
    _extendedIsDemo:    true,   // tells the UI these extended fields are demo
  };
}

// ── Service functions ─────────────────────────────────────────────────────────

/**
 * fetchModelMetrics — GET /metrics/model
 * Returns the latest model evaluation metrics.
 * Extended fields (MAPE, baselines, etc.) are always demo until the ML
 * team extends the API contract.
 */
export async function fetchModelMetrics() {
  return withDemoFallback(
    () => callApi((client) =>
      client.get('/metrics/model').then((r) => mapModelMetrics(r.data))
    ),
    () => ({ ...DEMO_MODEL_METRICS, source: 'DEMO — synthetic data', _extendedIsDemo: true })
  );
}

/**
 * fetchFeatureImportance — no backend endpoint yet.
 * Always returns demo data until the ML team adds this endpoint.
 * This function is a placeholder so the page already uses the right pattern.
 */
export async function fetchFeatureImportance() {
  return {
    data:   DEMO_FEATURE_IMPORTANCE,
    isDemo: true,
    error:  null,
    source: 'demo',
  };
}

/**
 * fetchTrainingHistory — no backend endpoint yet.
 * Always returns demo data until the ML team adds this endpoint.
 */
export async function fetchTrainingHistory() {
  return {
    data:   DEMO_TRAINING_HISTORY,
    isDemo: true,
    error:  null,
    source: 'demo',
  };
}
