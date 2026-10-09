/**
 * useApiData.js
 *
 * Generic React hook that wraps any async service function and manages
 * loading / error state consistently across all pages.
 *
 * KEY BEHAVIOUR: re-fetches automatically whenever `args` values change.
 * This is the fix for the hospital-selector not triggering a new fetch.
 *
 * Parameters:
 *   serviceFn  {Function}  — async service function
 *   args       {Array}     — arguments forwarded to serviceFn; re-fetch fires when these change
 *   options    {Object}
 *     fallback   {any}     — value while loading (default null)
 *     enabled    {boolean} — skip the call when false (default true)
 *
 * Returns: { data, loading, error, isDemo, source, refetch }
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export function useApiData(serviceFn, args = [], { fallback = null, enabled = true } = {}) {
  const [state, setState] = useState({
    data:    fallback,
    loading: enabled,
    error:   null,
    isDemo:  false,
    source:  null,
  });

  // Keep a current copy of args so the run fn always uses latest values
  const argsRef = useRef(args);
  argsRef.current = args;

  // Serialise args to a stable string — used as useEffect dependency
  // so ANY change to any arg value triggers a re-fetch
  const argsKey = JSON.stringify(args);

  const run = useCallback(async () => {
    if (!enabled) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const result = await serviceFn(...argsRef.current);
      setState({
        data:    result.data ?? fallback,
        loading: false,
        error:   result.isDemo ? null : (result.error ?? null),
        isDemo:  result.isDemo ?? false,
        source:  result.source,
      });
    } catch (err) {
      setState((s) => ({ ...s, loading: false, error: err, isDemo: false }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serviceFn, enabled, argsKey]);   // ← argsKey here is the fix

  useEffect(() => { run(); }, [run]);

  return { ...state, refetch: run };
}
