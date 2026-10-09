/**
 * useApiData.js
 *
 * Generic React hook that wraps any async service function and manages
 * loading / error / demo state consistently across all pages.
 *
 * Usage:
 *   const { data, loading, error, isDemo, refetch } =
 *     useApiData(fetchCurrentWeather, [], { fallback: null });
 *
 * Parameters:
 *   serviceFn  {Function}  — async service function to call (from *Service.js)
 *   args       {Array}     — arguments forwarded to serviceFn on every call
 *   options    {Object}
 *     fallback   {any}     — value used while loading (default null)
 *     enabled    {boolean} — set false to skip the call entirely (default true)
 *
 * Returned:
 *   data     — the resolved payload (or fallback while loading)
 *   loading  — true during the first fetch
 *   error    — ApiError | null
 *   isDemo   — true when data came from the demo fallback
 *   source   — 'api' | 'demo'
 *   refetch  — call to re-run the service function
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

  // Stable reference to args so effect doesn't loop on every render
  const argsRef = useRef(args);
  argsRef.current = args;

  const run = useCallback(async () => {
    if (!enabled) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const result = await serviceFn(...argsRef.current);
      setState({
        data:    result.data ?? fallback,
        loading: false,
        error:   result.isDemo ? null : (result.error ?? null),
        isDemo:  result.isDemo,
        source:  result.source,
      });
    } catch (err) {
      // Unexpected throw — services should not throw, but guard anyway
      setState((s) => ({
        ...s,
        loading: false,
        error:   err,
        isDemo:  false,
      }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serviceFn, enabled]);

  useEffect(() => { run(); }, [run]);

  return { ...state, refetch: run };
}
