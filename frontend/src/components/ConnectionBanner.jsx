import React from 'react';
import { BASE_URL } from '../api/client.js';
import { useHealthCheck, invalidateHealthCache } from '../api/useHealthCheck.js';

/**
 * ConnectionBanner — shown only when the backend or DB is unavailable.
 * Hidden entirely when everything is working correctly.
 */
function ConnectionBanner({ error, onRetry }) {
  const { isLive, dbConnected, loading } = useHealthCheck();

  if (loading) return null;

  // Everything is fine — hide the banner
  if (isLive && dbConnected) return null;

  // Backend not reachable
  if (!isLive) {
    const reason = error?.isTimeout
      ? `Request to ${BASE_URL} timed out.`
      : error?.status
      ? `Backend returned HTTP ${error.status}.`
      : `Cannot reach backend at ${BASE_URL}.`;

    return (
      <div className="conn-banner" role="alert" aria-live="assertive">
        <span className="conn-banner__icon" aria-hidden="true">🔌</span>
        <div className="conn-banner__body">
          <strong>Backend unavailable.</strong>{' '}
          <span className="conn-banner__reason">{reason}</span>
          {' '}Check that the backend is running on port 8000.
        </div>
        {onRetry && (
          <button
            className="conn-banner__retry btn btn-ghost"
            onClick={() => { invalidateHealthCache(); onRetry(); }}
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  // Backend up but DB tables missing
  if (!dbConnected) {
    return (
      <div className="conn-banner conn-banner--demo-mode" role="status" aria-live="polite">
        <span className="conn-banner__icon" aria-hidden="true">🗄️</span>
        <div className="conn-banner__body">
          <strong>Database not ready.</strong>{' '}
          <span className="conn-banner__reason">
            Run <code>database/migrations/FULL_SETUP.sql</code> in the{' '}
            <a
              href="https://supabase.com/dashboard/project/ehzqfftrhbvdklswicmj/sql/new"
              target="_blank"
              rel="noopener noreferrer"
            >
              Supabase SQL Editor
            </a>{' '}
            to create the tables and seed data.
          </span>
        </div>
        {onRetry && (
          <button
            className="conn-banner__retry btn btn-ghost"
            onClick={() => { invalidateHealthCache(); onRetry(); }}
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  return null;
}

export default ConnectionBanner;
