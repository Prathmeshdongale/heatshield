import React from 'react';
import { BASE_URL } from '../api/client.js';

/**
 * ConnectionBanner — shown at the top of a page when it is rendering demo data
 * instead of live API data.
 *
 * Props:
 *   isDemo   {boolean}   — show the banner
 *   error    {ApiError|null} — the error that caused the fallback (optional)
 *   onRetry  {Function}  — optional retry callback
 */
function ConnectionBanner({ isDemo, error, onRetry }) {
  if (!isDemo) return null;

  const isNetwork = error?.isNetwork;
  const isTimeout = error?.isTimeout;

  let reason = 'Backend not configured.';
  if (isNetwork) reason = `Cannot reach backend at ${BASE_URL}.`;
  else if (isTimeout) reason = `Request to ${BASE_URL} timed out.`;
  else if (error?.status) reason = `Backend returned HTTP ${error.status}.`;

  return (
    <div className="conn-banner" role="status" aria-live="polite">
      <span className="conn-banner__icon" aria-hidden="true">🔌</span>
      <div className="conn-banner__body">
        <strong>Showing demo data.</strong>
        {' '}
        <span className="conn-banner__reason">{reason}</span>
        {' '}
        Set <code>VITE_API_BASE_URL</code> in <code>.env</code> to connect the backend.
      </div>
      {onRetry && (
        <button className="conn-banner__retry btn btn-ghost" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export default ConnectionBanner;
