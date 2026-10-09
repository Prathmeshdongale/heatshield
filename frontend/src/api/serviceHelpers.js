/**
 * serviceHelpers.js
 *
 * Shared utilities used by every service module.
 *
 * The key contract every service returns:
 *
 *   { data, isDemo, error, source }
 *
 *   data    — the payload (real or demo)
 *   isDemo  — true when demo data was substituted
 *   error   — ApiError | null   (set only when backend was tried and failed,
 *                                 AND no demo fallback succeeded)
 *   source  — 'api' | 'demo'
 */

import apiClient, { ApiError } from './client.js';

/**
 * callApi — thin wrapper around apiClient that always returns a Result
 * instead of throwing, so services can decide whether to fall back.
 *
 * @param {Function} fn  — async function that calls apiClient and returns response.data
 * @returns {{ ok: boolean, data: any, error: ApiError|null }}
 */
export async function callApi(fn) {
  try {
    const data = await fn(apiClient);
    return { ok: true, data, error: null };
  } catch (err) {
    const apiErr = err instanceof ApiError
      ? err
      : new ApiError({ message: String(err), raw: err });
    return { ok: false, data: null, error: apiErr };
  }
}

/**
 * withDemoFallback — tries the real API; if it fails (network, timeout, or
 * non-2xx) it returns the demo data with isDemo: true.
 *
 * Pages receive a consistent shape and always know whether they are showing
 * real data or demo data — they never need to guess.
 *
 * @param {Function} apiFn   — () => Promise<data>  (calls callApi internally)
 * @param {Function} demoFn  — () => demoData
 * @returns {Promise<{ data, isDemo, error, source }>}
 */
export async function withDemoFallback(apiFn, demoFn) {
  const result = await apiFn();

  if (result.ok) {
    return { data: result.data, isDemo: false, error: null, source: 'api' };
  }

  // Log in dev so the team can see what failed
  if (import.meta.env.DEV) {
    console.warn(
      `[HeatShield] API call failed — falling back to demo data.\n` +
      `  Reason: ${result.error?.message}`
    );
  }

  return {
    data:   demoFn(),
    isDemo: true,
    error:  result.error,   // retained so UI can show "using demo, backend unavailable"
    source: 'demo',
  };
}
