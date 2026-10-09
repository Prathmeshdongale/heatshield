/**
 * useHealthCheck.js
 *
 * Polls GET /health once per page load to determine backend and DB status.
 * Result is cached at module level so multiple components share one request.
 *
 * Returns:
 *   isLive      — backend is reachable
 *   dbConnected — backend has a live Supabase connection
 *   demoMode    — backend is running in DEMO_MODE=true
 *   loading     — still fetching
 */

import { useState, useEffect } from 'react';
import { fetchHealth } from './alertsService.js';

// Module-level cache — shared across all hook instances on a page
let _cache = null;
let _promise = null;
const _listeners = new Set();

function getHealth() {
  if (_cache) return Promise.resolve(_cache);
  if (!_promise) {
    _promise = fetchHealth().then((result) => {
      const data = result.data ?? {};
      _cache = {
        isLive:      !result.isDemo && data.status === 'ok',
        dbConnected: !result.isDemo && !!data.db_connected,
        demoMode:    result.isDemo ? true : !!data.demo_mode,
        loading:     false,
      };
      _listeners.forEach((fn) => fn(_cache));
      return _cache;
    });
  }
  return _promise;
}

export function useHealthCheck() {
  const [state, setState] = useState(
    _cache ?? { isLive: false, dbConnected: false, demoMode: true, loading: true }
  );

  useEffect(() => {
    if (_cache) {
      setState(_cache);
      return;
    }
    const listener = (s) => setState(s);
    _listeners.add(listener);
    getHealth();
    return () => _listeners.delete(listener);
  }, []);

  return state;
}

/** Force a re-check (call after user clicks Retry) */
export function invalidateHealthCache() {
  _cache = null;
  _promise = null;
}
