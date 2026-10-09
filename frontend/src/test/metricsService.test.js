/**
 * metricsService.test.js
 * Tests for fetchModelMetrics, fetchFeatureImportance, fetchTrainingHistory.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../api/serviceHelpers.js', () => ({
  callApi: vi.fn(),
  withDemoFallback: vi.fn(),
}));

import { withDemoFallback } from '../api/serviceHelpers.js';
import {
  fetchModelMetrics,
  fetchFeatureImportance,
  fetchTrainingHistory,
} from '../api/metricsService.js';

const MOCK_METRICS = {
  model_name: 'GradientBoostingRegressor',
  trained_at: '2024-10-01T08:00:00Z',
  mae: 7.4, rmse: 9.8, r2: 0.87,
  source: 'api',
  mape: null, baseline_mae: null, baseline_rmse: null,
  feature_count: null, training_rows: null, training_duration_s: null,
  version: null, _extendedIsDemo: true,
};

describe('fetchModelMetrics', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns mapped metrics with required keys', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_METRICS, isDemo: false, error: null, source: 'api' });
    const result = await fetchModelMetrics();
    expect(result.data).toHaveProperty('model_name');
    expect(result.data).toHaveProperty('mae');
    expect(result.data).toHaveProperty('rmse');
    expect(result.data).toHaveProperty('r2');
  });

  it('flags extended fields as demo even when core data is from API', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_METRICS, isDemo: false, error: null, source: 'api' });
    const result = await fetchModelMetrics();
    expect(result.data._extendedIsDemo).toBe(true);
  });

  it('returns isDemo:true on fallback', async () => {
    withDemoFallback.mockResolvedValue({ data: { ...MOCK_METRICS, source: 'DEMO' }, isDemo: true, error: null, source: 'demo' });
    const result = await fetchModelMetrics();
    expect(result.isDemo).toBe(true);
  });
});

describe('fetchFeatureImportance', () => {
  it('always returns isDemo:true (no endpoint in contract)', async () => {
    const result = await fetchFeatureImportance();
    expect(result.isDemo).toBe(true);
    expect(result.source).toBe('demo');
  });

  it('returns an array of feature objects', async () => {
    const result = await fetchFeatureImportance();
    expect(Array.isArray(result.data)).toBe(true);
    result.data.forEach((f) => {
      expect(f).toHaveProperty('feature');
      expect(f).toHaveProperty('importance');
    });
  });
});

describe('fetchTrainingHistory', () => {
  it('always returns isDemo:true (no endpoint in contract)', async () => {
    const result = await fetchTrainingHistory();
    expect(result.isDemo).toBe(true);
  });

  it('returns an array of run objects', async () => {
    const result = await fetchTrainingHistory();
    expect(Array.isArray(result.data)).toBe(true);
    result.data.forEach((run) => {
      expect(run).toHaveProperty('run_id');
      expect(run).toHaveProperty('mae');
    });
  });
});
