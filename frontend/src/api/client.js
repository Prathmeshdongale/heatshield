/**
 * api/client.js
 *
 * Central Axios instance for the HeatShield frontend.
 *
 * RULES this file enforces:
 *  - Reads backend URL exclusively from VITE_API_BASE_URL (set in .env).
 *  - No Supabase keys, service-role keys, or any secrets belong here.
 *  - All outbound requests use this instance — never raw fetch/axios elsewhere.
 *  - Errors are normalised into ApiError objects so callers handle one shape.
 */

import axios from 'axios';

// ---------------------------------------------------------------------------
// Base URL — sourced from environment, never hardcoded secrets
// ---------------------------------------------------------------------------

export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 12_000,
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Normalised error class
// ---------------------------------------------------------------------------

/**
 * ApiError — wraps any HTTP or network error into a single shape.
 *
 * Properties:
 *   message     {string}         — human-readable summary
 *   status      {number|null}    — HTTP status code (null for network errors)
 *   endpoint    {string}         — the URL that failed
 *   isNetwork   {boolean}        — true when no response was received
 *   isTimeout   {boolean}        — true when the request timed out
 *   raw         {Error}          — original Axios error
 */
export class ApiError extends Error {
  constructor({ message, status = null, endpoint = '', isNetwork = false, isTimeout = false, raw }) {
    super(message);
    this.name      = 'ApiError';
    this.status    = status;
    this.endpoint  = endpoint;
    this.isNetwork = isNetwork;
    this.isTimeout = isTimeout;
    this.raw       = raw;
  }
}

// ---------------------------------------------------------------------------
// Response interceptor — normalise every error into ApiError
// ---------------------------------------------------------------------------

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const endpoint = error.config?.url ?? '(unknown)';

    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return Promise.reject(
        new ApiError({
          message:   `Request timed out: ${endpoint}`,
          endpoint,
          isTimeout: true,
          isNetwork: false,
          raw:       error,
        })
      );
    }

    if (!error.response) {
      // Network error — backend not reachable
      return Promise.reject(
        new ApiError({
          message:   `Network error — backend not reachable at ${BASE_URL}`,
          endpoint,
          isNetwork: true,
          raw:       error,
        })
      );
    }

    const status = error.response.status;
    const detail = error.response.data?.detail ?? error.response.statusText ?? 'Unknown error';
    return Promise.reject(
      new ApiError({
        message:   `HTTP ${status} from ${endpoint}: ${detail}`,
        status,
        endpoint,
        isNetwork: false,
        raw:       error,
      })
    );
  }
);

export default apiClient;
