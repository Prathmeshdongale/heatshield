import React from 'react';
import { useLocation } from 'react-router-dom';
import { useHealthCheck } from '../../api/useHealthCheck.js';

/**
 * Header — top bar showing page title, live timestamp, and connection status.
 *
 * Status badge states:
 *   ● LIVE + DB   — backend connected, Supabase tables exist
 *   ● API / DB PENDING — backend up but DB tables missing
 *   ● LIVE        — backend connected, DEMO_MODE=true
 *   Offline       — backend not reachable
 */

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/forecasts': 'Demand Forecasts',
  '/hospitals': 'Hospital Monitoring',
  '/heatwave':  'Heatwave Analysis',
  '/metrics':   'Model Metrics',
  '/settings':  'Settings',
};

function Header() {
  const { pathname }                        = useLocation();
  const { isLive, dbConnected, demoMode, modelLoaded } = useHealthCheck();
  const title                               = PAGE_TITLES[pathname] ?? 'HeatShield';

  const now = new Date().toLocaleString('en-AU', {
    weekday: 'short',
    year:    'numeric',
    month:   'short',
    day:     'numeric',
    hour:    '2-digit',
    minute:  '2-digit',
  });

  return (
    <header className="header" role="banner">
      <h1 className="header-title">{title}</h1>
      <div className="header-meta">
        <span className="header-timestamp" aria-label="Current date and time">
          {now}
        </span>
        {isLive && dbConnected && modelLoaded ? (
          <span className="live-badge"
            aria-label="Backend + DB + ML Model all live"
            title="Backend connected — Supabase DB + ML Model v1.0.0 active">
            ● LIVE + ML
          </span>
        ) : isLive && dbConnected ? (
          <span className="live-badge"
            aria-label="Backend and DB connected"
            title="Backend + Supabase connected. ML model loading…"
            style={{ backgroundColor: '#3b82f6', color: '#fff' }}>
            ● LIVE + DB
          </span>
        ) : isLive && !demoMode ? (
          <span
            className="live-badge live-badge--partial"
            aria-label="Backend connected, DB setup pending"
            title="Backend reachable but Supabase tables not yet created. Run FULL_SETUP.sql in the Supabase SQL Editor."
            style={{ backgroundColor: '#f59e0b', color: '#fff' }}
          >
            ● API / DB PENDING
          </span>
        ) : isLive ? (
          <span
            className="live-badge"
            aria-label="Backend connected in demo mode"
            title="Backend connected — DEMO_MODE=true on the server"
            style={{ backgroundColor: '#f59e0b', color: '#fff' }}
          >
            ● LIVE (DEMO)
          </span>
        ) : (
          <span className="status-badge-offline" aria-label="Backend not reachable">
            Offline
          </span>
        )}
      </div>
    </header>
  );
}

export default Header;
