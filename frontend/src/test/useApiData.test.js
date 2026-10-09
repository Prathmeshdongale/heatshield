/**
 * useApiData.test.js
 * Tests for the generic useApiData hook covering:
 *   - loading state
 *   - successful data
 *   - demo mode
 *   - refetch
 *   - disabled flag
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApiData } from '../api/useApiData.js';

const MOCK_DATA = [{ id: 1, name: 'test' }];

function makeService(payload) {
  return vi.fn().mockResolvedValue(payload);
}

describe('useApiData', () => {
  it('starts in loading state', () => {
    const svc = makeService({ data: MOCK_DATA, isDemo: false, error: null, source: 'api' });
    const { result } = renderHook(() => useApiData(svc, []));
    expect(result.current.loading).toBe(true);
  });

  it('resolves with data and loading:false after service resolves', async () => {
    const svc = makeService({ data: MOCK_DATA, isDemo: false, error: null, source: 'api' });
    const { result } = renderHook(() => useApiData(svc, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(MOCK_DATA);
    expect(result.current.isDemo).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets isDemo:true when service returns demo', async () => {
    const svc = makeService({ data: MOCK_DATA, isDemo: true, error: null, source: 'demo' });
    const { result } = renderHook(() => useApiData(svc, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.isDemo).toBe(true);
    expect(result.current.source).toBe('demo');
  });

  it('uses fallback value while loading', () => {
    const svc = makeService({ data: MOCK_DATA, isDemo: false, error: null, source: 'api' });
    const { result } = renderHook(() => useApiData(svc, [], { fallback: [] }));
    expect(result.current.data).toEqual([]);
  });

  it('does not fetch when enabled:false', () => {
    const svc = makeService({ data: MOCK_DATA, isDemo: false, error: null, source: 'api' });
    const { result } = renderHook(() => useApiData(svc, [], { enabled: false }));
    expect(svc).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('exposes a refetch function that re-runs the service', async () => {
    const svc = makeService({ data: MOCK_DATA, isDemo: false, error: null, source: 'api' });
    const { result } = renderHook(() => useApiData(svc, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(svc).toHaveBeenCalledTimes(1);
    await act(async () => { result.current.refetch(); });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(svc).toHaveBeenCalledTimes(2);
  });

  it('sets error when service rejects unexpectedly', async () => {
    const svc = vi.fn().mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useApiData(svc, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeTruthy();
  });
});
