import React from 'react';

/**
 * AlertsPanel — displays a list of recent system alerts.
 *
 * Props:
 *   alerts   {Array}   — array of alert objects
 *   loading  {boolean} — skeleton state
 *   error    {boolean} — error state
 */

const SEVERITY_META = {
  critical: { color: '#7c3aed', bg: '#faf5ff', icon: '🚨', label: 'Critical' },
  high:     { color: '#ef4444', bg: '#fef2f2', icon: '🔴', label: 'High'     },
  medium:   { color: '#f59e0b', bg: '#fffbeb', icon: '🟡', label: 'Medium'   },
  low:      { color: '#22c55e', bg: '#f0fdf4', icon: '🟢', label: 'Low'      },
};

function timeAgo(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const mins   = Math.floor(diffMs / 60_000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function AlertItem({ alert }) {
  const meta = SEVERITY_META[alert.severity] ?? SEVERITY_META.low;
  return (
    <li
      className="alert-item"
      style={{ borderLeftColor: meta.color }}
      aria-label={`${meta.label} alert: ${alert.message}`}
    >
      <div className="alert-item__top">
        <span className="alert-item__icon" aria-hidden="true">{meta.icon}</span>
        <span className="alert-item__severity" style={{ color: meta.color }}>
          {meta.label}
        </span>
        <span className="alert-item__facility">{alert.facility}</span>
        <time className="alert-item__time" dateTime={alert.timestamp}>
          {timeAgo(alert.timestamp)}
        </time>
      </div>
      <p className="alert-item__message">{alert.message}</p>
    </li>
  );
}

function SkeletonAlerts() {
  return Array.from({ length: 3 }, (_, i) => (
    <li key={i} className="alert-item" aria-hidden="true">
      <div className="skeleton skeleton--text-sm" style={{ width: '40%', marginBottom: 6 }} />
      <div className="skeleton skeleton--text-sm" style={{ width: '90%' }} />
    </li>
  ));
}

function AlertsPanel({ alerts = [], loading = false, error = false }) {
  return (
    <section className="alerts-panel" aria-label="Recent alerts">
      <div className="chart-header">
        <h2 className="chart-title">Recent Alerts</h2>
        <span className="demo-badge">DEMO DATA</span>
      </div>

      {error && (
        <p className="table-state table-state--error" role="alert">⚠ Could not load alerts.</p>
      )}

      {!error && (
        <ul className="alerts-list" role="list">
          {loading
            ? <SkeletonAlerts />
            : alerts.length === 0
              ? <li className="table-state">No recent alerts.</li>
              : alerts.map((a) => <AlertItem key={a.id} alert={a} />)
          }
        </ul>
      )}
    </section>
  );
}

export default AlertsPanel;
