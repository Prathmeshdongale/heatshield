import React from 'react';

/**
 * StatusBanner — full-width top-of-page risk status bar.
 *
 * Props:
 *   riskLevel    {string}  — "low" | "medium" | "high" | "critical"
 *   message      {string}  — descriptive status message
 *   freshness    {number}  — minutes since last data refresh
 *   loading      {boolean} — skeleton state
 */

const RISK_META = {
  low:      { color: '#166534', bg: '#dcfce7', border: '#86efac', icon: '✅', label: 'Low Risk'      },
  medium:   { color: '#92400e', bg: '#fef3c7', border: '#fcd34d', icon: '⚠️',  label: 'Moderate Risk' },
  high:     { color: '#991b1b', bg: '#fee2e2', border: '#fca5a5', icon: '🔴', label: 'High Risk'     },
  critical: { color: '#4c1d95', bg: '#f3e8ff', border: '#c084fc', icon: '🚨', label: 'Critical Risk' },
};

function StatusBanner({ riskLevel = 'medium', message, freshness, loading = false }) {
  if (loading) {
    return (
      <div className="status-banner status-banner--skeleton" aria-busy="true">
        <div className="skeleton skeleton--text-md" style={{ width: 300 }} />
      </div>
    );
  }

  const meta = RISK_META[riskLevel] ?? RISK_META.medium;

  return (
    <div
      className="status-banner"
      style={{ backgroundColor: meta.bg, borderColor: meta.border, color: meta.color }}
      role="status"
      aria-live="polite"
      aria-label={`Overall system status: ${meta.label}`}
    >
      <span className="status-banner__icon" aria-hidden="true">{meta.icon}</span>
      <div className="status-banner__body">
        <strong className="status-banner__level">{meta.label}</strong>
        {message && <span className="status-banner__message"> — {message}</span>}
      </div>
      <div className="status-banner__meta">
        {freshness != null && (
          <span className="status-banner__freshness">
            🕐 Data refreshed {freshness} min ago
          </span>
        )}
        <span className="demo-badge">DEMO DATA</span>
      </div>
    </div>
  );
}

export default StatusBanner;
