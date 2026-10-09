/**
 * weatherService.test.js
 * Tests for fetchCurrentWeather and fetchWeatherHistory.
 * Mocks withDemoFallback so we can control API success / failure independently
 * of Axios network behaviour.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the helpers module before importing the service
vi.mock('../api/serviceHelpers.js', () => ({
  callApi: vi.fn(),
  withDemoFallback: vi.fn(),
}));

import { withDemoFallback } from '../api/serviceHelpers.js';
import { fetchCurrentWeather, fetchWeatherHistory } from '../api/weatherService.js';

const MOCK_CURRENT = {
  timestamp: '2024-10-01T10:00:00Z',
  temp_c: 34,
  humidity_pct: 70,
  heat_index: 42,
  source: 'api',
};

const MOCK_HISTORY = [
  { date: '2024-09-29', temp_c: 31, heat_index: 38, humidity_pct: 65, source: 'api' },
  { date: '2024-09-30', temp_c: 33, heat_index: 40, humidity_pct: 68, source: 'api' },
];

describe('fetchCurrentWeather', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns real data shape when API succeeds', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_CURRENT, isDemo: false, error: null, source: 'api' });
    const result = await fetchCurrentWeather();
    expect(result.isDemo).toBe(false);
    expect(result.data.temp_c).toBe(34);
    expect(result.data.heat_index).toBe(42);
  });

  it('returns isDemo:true when API fails', async () => {
    withDemoFallback.mockResolvedValue({ data: { ...MOCK_CURRENT, source: 'DEMO' }, isDemo: true, error: null, source: 'demo' });
    const result = await fetchCurrentWeather();
    expect(result.isDemo).toBe(true);
    expect(result.source).toBe('demo');
  });

  it('calls withDemoFallback exactly once', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_CURRENT, isDemo: false, error: null, source: 'api' });
    await fetchCurrentWeather();
    expect(withDemoFallback).toHaveBeenCalledTimes(1);
  });
});

describe('fetchWeatherHistory', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns an array when API succeeds', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_HISTORY, isDemo: false, error: null, source: 'api' });
    const result = await fetchWeatherHistory(7);
    expect(Array.isArray(result.data)).toBe(true);
    expect(result.data.length).toBe(2);
  });

  it('all rows have required keys', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_HISTORY, isDemo: false, error: null, source: 'api' });
    const result = await fetchWeatherHistory(7);
    result.data.forEach((row) => {
      expect(row).toHaveProperty('date');
      expect(row).toHaveProperty('temp_c');
      expect(row).toHaveProperty('heat_index');
      expect(row).toHaveProperty('humidity_pct');
    });
  });
});
