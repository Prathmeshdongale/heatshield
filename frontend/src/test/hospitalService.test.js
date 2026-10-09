/**
 * hospitalService.test.js
 * Tests for fetchHospitals, fetchHospitalRisk, fetchAllHospitalsWithRisk.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../api/serviceHelpers.js', () => ({
  callApi: vi.fn(),
  withDemoFallback: vi.fn(),
}));

import { withDemoFallback } from '../api/serviceHelpers.js';
import {
  fetchHospitals,
  fetchHospitalRisk,
  fetchAllHospitalsWithRisk,
} from '../api/hospitalService.js';

const MOCK_HOSPITALS = [
  { hospital_id: 'H001', name: 'City General', region: 'North', total_beds: 400, icu_beds: 40, source: 'api' },
  { hospital_id: 'H002', name: 'Eastside MC',  region: 'East',  total_beds: 280, icu_beds: 28, source: 'api' },
];

const MOCK_RISK_H001 = {
  hospital_id: 'H001', date: '2024-10-01', occupancy_pct: 88,
  risk_level: 'critical', predicted_surge: 18, source: 'api',
};

const MOCK_RISK_H002 = {
  hospital_id: 'H002', date: '2024-10-01', occupancy_pct: 76,
  risk_level: 'high', predicted_surge: 12, source: 'api',
};

describe('fetchHospitals', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns array with hospital_id field', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_HOSPITALS, isDemo: false, error: null, source: 'api' });
    const result = await fetchHospitals();
    expect(Array.isArray(result.data)).toBe(true);
    result.data.forEach((h) => expect(h).toHaveProperty('hospital_id'));
  });

  it('returns isDemo:true when demo fallback is used', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_HOSPITALS, isDemo: true, error: null, source: 'demo' });
    const result = await fetchHospitals();
    expect(result.isDemo).toBe(true);
  });
});

describe('fetchHospitalRisk', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns risk object with required keys', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_RISK_H001, isDemo: false, error: null, source: 'api' });
    const result = await fetchHospitalRisk('H001');
    expect(result.data).toHaveProperty('hospital_id');
    expect(result.data).toHaveProperty('occupancy_pct');
    expect(result.data).toHaveProperty('risk_level');
    expect(result.data).toHaveProperty('predicted_surge');
  });

  it('risk_level is one of the agreed values', async () => {
    withDemoFallback.mockResolvedValue({ data: MOCK_RISK_H001, isDemo: false, error: null, source: 'api' });
    const result = await fetchHospitalRisk('H001');
    expect(['low', 'medium', 'high', 'critical']).toContain(result.data.risk_level);
  });
});

describe('fetchAllHospitalsWithRisk', () => {
  beforeEach(() => vi.clearAllMocks());

  it('merges hospital metadata with risk data', async () => {
    withDemoFallback
      .mockResolvedValueOnce({ data: MOCK_HOSPITALS, isDemo: false, error: null, source: 'api' })
      .mockResolvedValueOnce({ data: MOCK_RISK_H001, isDemo: false, error: null, source: 'api' })
      .mockResolvedValueOnce({ data: MOCK_RISK_H002, isDemo: false, error: null, source: 'api' });
    const result = await fetchAllHospitalsWithRisk();
    expect(result.data.length).toBe(2);
    expect(result.data[0]).toHaveProperty('name');
    expect(result.data[0]).toHaveProperty('risk_level');
  });

  it('returns empty array and isDemo:true when hospital list is empty', async () => {
    withDemoFallback.mockResolvedValueOnce({ data: [], isDemo: true, error: null, source: 'demo' });
    const result = await fetchAllHospitalsWithRisk();
    expect(result.data).toEqual([]);
    expect(result.isDemo).toBe(true);
  });

  it('isDemo:true when any sub-call is demo', async () => {
    withDemoFallback
      .mockResolvedValueOnce({ data: MOCK_HOSPITALS, isDemo: false, error: null, source: 'api' })
      .mockResolvedValueOnce({ data: MOCK_RISK_H001, isDemo: true,  error: null, source: 'demo' })
      .mockResolvedValueOnce({ data: MOCK_RISK_H002, isDemo: false, error: null, source: 'api' });
    const result = await fetchAllHospitalsWithRisk();
    expect(result.isDemo).toBe(true);
  });
});
