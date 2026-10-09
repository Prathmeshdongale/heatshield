/**
 * serviceHelpers.test.js
 * Tests for callApi and withDemoFallback.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { callApi, withDemoFallback } from '../api/serviceHelpers.js';
import { ApiError } from '../api/client.js';

// ── callApi ───────────────────────────────────────────────────────────────────

describe('callApi', () => {
  it('returns ok:true with data when fn resolves', async () => {
    const fn = vi.fn().mockResolvedValue({ name: 'result' });
    const result = await callApi(fn);
    expect(result.ok).toBe(true);
    expect(result.data).toEqual({ name: 'result' });
    expect(result.error).toBeNull();
  });

  it('returns ok:false with ApiError when fn throws an ApiError', async () => {
    const apiErr = new ApiError({ message: 'network fail', raw: new Error() });
    const fn = vi.fn().mockRejectedValue(apiErr);
    const result = await callApi(fn);
    expect(result.ok).toBe(false);
    expect(result.data).toBeNull();
    expect(result.error).toBeInstanceOf(ApiError);
    expect(result.error.message).toBe('network fail');
  });

  it('wraps a plain Error into ApiError when fn throws', async () => {
    const fn = vi.fn().mockRejectedValue(new Error('plain error'));
    const result = await callApi(fn);
    expect(result.ok).toBe(false);
    expect(result.error).toBeInstanceOf(ApiError);
  });
});

// ── withDemoFallback ──────────────────────────────────────────────────────────

describe('withDemoFallback', () => {
  const demoFn = () => [{ date: '2024-01-01', source: 'DEMO' }];

  it('returns real data with isDemo:false when API call succeeds', async () => {
    const apiFn = vi.fn().mockResolvedValue({ ok: true, data: [{ date: '2024-01-01' }], error: null });
    const result = await withDemoFallback(apiFn, demoFn);
    expect(result.isDemo).toBe(false);
    expect(result.source).toBe('api');
    expect(result.data).toEqual([{ date: '2024-01-01' }]);
    expect(result.error).toBeNull();
  });

  it('returns demo data with isDemo:true when API call fails', async () => {
    const apiErr = new ApiError({ message: 'Network error', isNetwork: true, raw: new Error() });
    const apiFn = vi.fn().mockResolvedValue({ ok: false, data: null, error: apiErr });
    const result = await withDemoFallback(apiFn, demoFn);
    expect(result.isDemo).toBe(true);
    expect(result.source).toBe('demo');
    expect(result.data).toEqual(demoFn());
    expect(result.error).toBeInstanceOf(ApiError);
  });

  it('preserves the original error in the result even when demo is used', async () => {
    const apiErr = new ApiError({ message: 'HTTP 503', status: 503, raw: new Error() });
    const apiFn = vi.fn().mockResolvedValue({ ok: false, data: null, error: apiErr });
    const result = await withDemoFallback(apiFn, demoFn);
    expect(result.error.status).toBe(503);
  });
});
