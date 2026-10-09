/**
 * forecastService.test.js
 * Tests for fetchHistoricalDemand, fetchDemandForecast, fetchCombinedDemandSeries.
 *
 * fetchHistoricalDemand always returns demo data (no backend history endpoint).
 * fetchDemandForecast uses withDemoFallback against the real /forecasts endpoint.
 * fetchCombinedDemandSeries merges the two.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../api/serviceHelpers.js', () => ({
  callApi: vi.fn(),
  withDemoFallback: vi.fn(),
}));

import { withDemoFallback } from '../api/serviceHelpers.js';
import {
  fetchHistoricalDemand,
  fetchDemandForecast,
  fetchCombinedDemandSeries,
} from '../api/forecastService.js';

const MOCK_FORECAST = [
  { date: '2024-10-02', admissions: null, er_visits: null, predicted_admissions: 105, upper_ci: 115, lower_ci: 95, confidence: 0.85, type: 'forecast', source: 'api' },
  { date: '2024-10-03', admissions: null, er_visits: null, predicted_admissions: 110, upper_ci: 122, lower_ci: 98, confidence: 0.82, type: 'forecast', source: 'api' },
];

// ── fetchHistoricalDemand ──────────────────────────────────────────────────
// No backend endpoint — always returns demo data without calling withDemoFallback.

describe('fetchHistoricalDemand', () => {
  it('always returns isDemo:true (no backend history endpoint)', async () => {
    const result = await fetchHistoricalDemand(14);
    expect(result.isDemo).toBe(true);
    expect(result.source).toBe('demo');
  });

  it('returns historical rows with type:historical', async () => {
    const result = await fetchHistoricalDemand(14);
    expect(result.data.every((r) => r.type === 'historical')).toBe(true);
  });

  it('rows have admissions and er_visits', async () => {
    const result = await fetchHistoricalDemand(14);
    result.data.forEach((r) => {
      expect(r).toHaveProperty('admissions');
      expect(r).toHaveProperty('er_visits');
    });
  });

  it('respects the days parameter', async () => {
    const result5  = await fetchHistoricalDemand(5);
    const result10 = await fetchHistoricalDemand(10);
    expect(result5.data.length).toBeLessThanOrEqual(5);
    expect(result10.data.length).toBeLessThanOrEqual(10);
    expect(result10.data.length).toBeGreaterThanOrEqual(result5.data.length);
  });
});

// ── fetchDemandForecast ────────────────────────────────────────────────────

describe('fetchDemandForecast', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns forecast rows with type:forecast', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_FORECAST, isDemo: false, error: null, source: 'api' });
    const result = await fetchDemandForecast(7);
    expect(result.data.every((r) => r.type === 'forecast')).toBe(true);
  });

  it('rows have predicted_admissions', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_FORECAST, isDemo: false, error: null, source: 'api' });
    const result = await fetchDemandForecast(7);
    result.data.forEach((r) => {
      expect(r).toHaveProperty('predicted_admissions');
    });
  });

  it('returns isDemo:true when fallback is used', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_FORECAST, isDemo: true, error: null, source: 'demo' });
    const result = await fetchDemandForecast(7);
    expect(result.isDemo).toBe(true);
  });
});

// ── fetchCombinedDemandSeries ──────────────────────────────────────────────
// History is always demo; forecast may be real or demo.

describe('fetchCombinedDemandSeries', () => {
  beforeEach(() => vi.clearAllMocks());

  it('merges history (demo) and forecast into a single array', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_FORECAST, isDemo: false, error: null, source: 'api' });
    const result = await fetchCombinedDemandSeries(14, 2);
    // History returns ≤14 rows; forecast returns 2
    expect(result.data.length).toBeGreaterThan(0);
    expect(result.data.some((r) => r.type === 'historical')).toBe(true);
    expect(result.data.some((r) => r.type === 'forecast')).toBe(true);
  });

  it('isDemo:false when forecast sub-call is from API', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_FORECAST, isDemo: false, error: null, source: 'api' });
    const result = await fetchCombinedDemandSeries(14, 7);
    // history is demo but forecast is real → combined isDemo=false
    expect(result.isDemo).toBe(false);
    expect(result.source).toBe('api');
  });

  it('isDemo:true when forecast sub-call is also demo', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_FORECAST, isDemo: true, error: null, source: 'demo' });
    const result = await fetchCombinedDemandSeries(14, 7);
    expect(result.isDemo).toBe(true);
    expect(result.source).toBe('demo');
  });

  it('still returns data when forecast returns empty array', async () => {
    withDemoFallback.mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' });
    const result = await fetchCombinedDemandSeries(7, 7);
    // History still contributes rows
    expect(result.data.some((r) => r.type === 'historical')).toBe(true);
  });
});
