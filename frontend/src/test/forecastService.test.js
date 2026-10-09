/**
 * forecastService.test.js
 * Tests for fetchHistoricalDemand, fetchDemandForecast, fetchCombinedDemandSeries.
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

const MOCK_HISTORY = [
  { date: '2024-09-28', admissions: 90, er_visits: 160, predicted_admissions: null, upper_ci: null, lower_ci: null, type: 'historical', source: 'api' },
  { date: '2024-09-29', admissions: 95, er_visits: 165, predicted_admissions: null, upper_ci: null, lower_ci: null, type: 'historical', source: 'api' },
];

const MOCK_FORECAST = [
  { date: '2024-10-02', admissions: null, er_visits: null, predicted_admissions: 105, upper_ci: 115, lower_ci: 95, confidence: 0.85, type: 'forecast', source: 'api' },
  { date: '2024-10-03', admissions: null, er_visits: null, predicted_admissions: 110, upper_ci: 122, lower_ci: 98, confidence: 0.82, type: 'forecast', source: 'api' },
];

describe('fetchHistoricalDemand', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns historical rows with type:historical', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_HISTORY, isDemo: false, error: null, source: 'api' });
    const result = await fetchHistoricalDemand(14);
    expect(result.data.every((r) => r.type === 'historical')).toBe(true);
  });

  it('rows have admissions and er_visits', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_HISTORY, isDemo: false, error: null, source: 'api' });
    const result = await fetchHistoricalDemand(14);
    result.data.forEach((r) => {
      expect(r).toHaveProperty('admissions');
      expect(r).toHaveProperty('er_visits');
    });
  });
});

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
});

describe('fetchCombinedDemandSeries', () => {
  beforeEach(() => vi.clearAllMocks());

  it('merges history and forecast into a single array', async () => {
    withDemoFallback
      .mockResolvedValueOnce({ data: MOCK_HISTORY,  isDemo: false, error: null, source: 'api' })
      .mockResolvedValueOnce({ data: MOCK_FORECAST, isDemo: false, error: null, source: 'api' });
    const result = await fetchCombinedDemandSeries(14, 7);
    expect(result.data.length).toBe(MOCK_HISTORY.length + MOCK_FORECAST.length);
    expect(result.isDemo).toBe(false);
    expect(result.source).toBe('api');
  });

  it('isDemo:true when both sub-calls are demo', async () => {
    withDemoFallback
      .mockResolvedValueOnce({ data: MOCK_HISTORY,  isDemo: true, error: null, source: 'demo' })
      .mockResolvedValueOnce({ data: MOCK_FORECAST, isDemo: true, error: null, source: 'demo' });
    const result = await fetchCombinedDemandSeries(14, 7);
    expect(result.isDemo).toBe(true);
  });

  it('isDemo:false when at least one sub-call is real', async () => {
    withDemoFallback
      .mockResolvedValueOnce({ data: MOCK_HISTORY,  isDemo: false, error: null, source: 'api' })
      .mockResolvedValueOnce({ data: MOCK_FORECAST, isDemo: true,  error: null, source: 'demo' });
    const result = await fetchCombinedDemandSeries(14, 7);
    expect(result.isDemo).toBe(false);
  });

  it('returns empty data array when both calls return empty', async () => {
    withDemoFallback
      .mockResolvedValueOnce({ data: [], isDemo: true, error: null, source: 'demo' })
      .mockResolvedValueOnce({ data: [], isDemo: true, error: null, source: 'demo' });
    const result = await fetchCombinedDemandSeries(14, 7);
    expect(result.data).toEqual([]);
  });
});
