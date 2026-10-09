import React from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Header — top bar that shows the current page title and a live timestamp.
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
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? 'HeatShield';

  const now = new Date().toLocaleString('en-AU', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <header className="header" role="banner">
      <h1 className="header-title">{title}</h1>
      <div className="header-meta">
        <span className="header-timestamp" aria-label="Current date and time">
          {now}
        </span>
        <span className="demo-badge" aria-label="Data source: demo data">
          DEMO DATA
        </span>
      </div>
    </header>
  );
}

export default Header;
