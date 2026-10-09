/**
 * useHealthCheck.js
 * Polls GET /health once per session. Result cached at module level.
 * Returns: { isLive, dbConnected, demoMode, modelLoaded, modelVersion, loading }
 */
import { useState, useEffect } from 'react';
import { fetchHealth } from './alertsService.js';

let _cache = null;
let _promise = null;
const _listeners = new Set();

function getHealth() {
  if (_cache) return Promise.resolve(_cache);
  if (!_promise) {
    _promise = fetchHealth().then((result) => {
      const d = result.data ?? {};
      _cache = {
        isLive:       !result.isDemo && d.status === 'ok',
        dbConnected:  !result.isDemo && !!d.db_connected,
        demoMode:     result.isDemo ? true : !!d.demo_mode,
        modelLoaded:  !result.isDemo && !!d.model_loaded,
        modelVersion: d.model_version ?? null,
        loading:      false,
      };
      _listeners.forEach((fn) => fn(_cache));
      return _cache;
    });
  }
  return _promise;
}

export function useHealthCheck() {
  const [state, setState] = useState(
    _cache ?? { isLive: false, dbConnected: false, demoMode: true,
                modelLoaded: false, modelVersion: null, loading: true }
  );
  useEffect(() => {
    if (_cache) { setState(_cache); return; }
    const listener = (s) => setState(s);
    _listeners.add(listener);
    getHealth();
    return () => _listeners.delete(listener);
  }, []);
  return state;
}

export function invalidateHealthCache() {
  _cache = null;
  _promise = null;
}
