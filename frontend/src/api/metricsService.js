/**
 * metricsService.js — fetches model metrics directly from the API. No demo fallback.
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

function mapModelMetrics(raw) {
  return {
    model_name:    raw.model_version ?? 'v1.0.0',
    version:       raw.model_version ?? 'v1.0.0',
    trained_at:    raw.evaluated_on,
    mae:           typeof raw.mae  === 'number' ? Math.round(raw.mae  * 100) / 100 : raw.mae,
    rmse:          typeof raw.rmse === 'number' ? Math.round(raw.rmse * 100) / 100 : raw.rmse,
    r2:            typeof raw.r2   === 'number' ? Math.round(raw.r2   * 10000) / 10000 : raw.r2,
    feature_count: raw.feature_count,
    source:        'api',
  };
}

export async function fetchModelMetrics() {
  return call((c) => c.get('/metrics').then((r) => mapModelMetrics(r.data?.data ?? {})));
}

export async function fetchFeatureImportance() {
  return { data: [], error: null, isDemo: false, source: 'api' };
}

export async function fetchTrainingHistory() {
  return { data: [], error: null, isDemo: false, source: 'api' };
}
