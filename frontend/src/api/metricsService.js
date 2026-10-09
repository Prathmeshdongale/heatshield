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
    model_name:    raw.model_version,
    version:       raw.model_version,
    trained_at:    raw.evaluated_on,
    mae:           raw.mae,
    rmse:          raw.rmse,
    r2:            raw.r2,
    feature_count: raw.feature_count,
    mape:          null,
    baseline_mae:  null,
    baseline_rmse: null,
    training_rows: null,
    training_duration_s: null,
    source: 'api',
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
