import React from 'react';

/**
 * RiskTable — hospital capacity risk table.
 *
 * Props:
 *   rows     {Array}   — array of hospital risk objects
 *   loading  {boolean} — skeleton state
 *   error    {boolean} — error state
 */

const RISK_META = {
  // UI-side keys (from normalised mapper in hospitalService)
  low:      { color: '#22c55e', bg: '#f0fdf4' },
  medium:   { color: '#f59e0b', bg: '#fffbeb' },
  high:     { color: '#ef4444', bg: '#fef2f2' },
  critical: { color: '#7c3aed', bg: '#faf5ff' },
  // Backend-side aliases (safety net)
  green:    { color: '#22c55e', bg: '#f0fdf4' },
  amber:    { color: '#f59e0b', bg: '#fffbeb' },
  red:      { color: '#ef4444', bg: '#fef2f2' },
};

function RiskBadge({ level }) {
  const meta = RISK_META[level] ?? { color: '#94a3b8', bg: '#f8fafc' };
  return (
    <span
      className="risk-badge"
      style={{ backgroundColor: meta.color }}
      aria-label={`Risk level: ${level}`}
    >
      {level?.toUpperCase() ?? 'UNKNOWN'}
    </span>
  );
}

/** Compact horizontal bar showing occupancy % */
function OccupancyBar({ value }) {
  if (value == null) return <span>—</span>;
  const meta = value >= 90 ? RISK_META.critical
             : value >= 75 ? RISK_META.high
             : value >= 60 ? RISK_META.medium
             : RISK_META.low;
  return (
    <div className="occ-bar-wrapper" aria-label={`${value}% occupied`}>
      <div
        className="occ-bar-fill"
        style={{ width: `${Math.min(value, 100)}%`, backgroundColor: meta.color }}
      />
      <span className="occ-bar-label">{value}%</span>
    </div>
  );
}

function SkeletonRows() {
  return Array.from({ length: 4 }, (_, i) => (
    <tr key={i} aria-hidden="true">
      {Array.from({ length: 6 }, (__, j) => (
        <td key={j}><div className="skeleton skeleton--text-sm" /></td>
      ))}
    </tr>
  ));
}

function RiskTable({ rows = [], loading = false, error = false }) {
  return (
    <div className="risk-table-wrapper" role="region" aria-label="Hospital capacity risk table">
      <div className="risk-table-header">
        <h2 className="chart-title" style={{ margin: 0 }}>Hospital Capacity &amp; Risk</h2>
      </div>

      {error && (
        <p className="table-state table-state--error" role="alert">
          ⚠ Could not load hospital data.
        </p>
      )}

      {!error && (
        <table className="risk-table">
          <thead>
            <tr>
              <th scope="col">Hospital</th>
              <th scope="col">Region</th>
              <th scope="col">Occupancy</th>
              <th scope="col">ICU %</th>
              <th scope="col">Risk Level</th>
              <th scope="col">Pred. Surge</th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? <SkeletonRows />
              : rows.length === 0
                ? (
                  <tr>
                    <td colSpan={6} className="table-state">No hospital data available.</td>
                  </tr>
                )
                : rows.map((row) => (
                  <tr key={row.hospital_id}>
                    <td className="risk-table__name">{row.name ?? row.hospital_id}</td>
                    <td>{row.region ?? '—'}</td>
                    <td><OccupancyBar value={row.occupancy_pct} /></td>
                    <td>
                      <OccupancyBar value={row.icu_occupancy_pct} />
                    </td>
                    <td><RiskBadge level={row.risk_level} /></td>
                    <td className="risk-table__surge">
                      {row.predicted_surge != null ? `+${row.predicted_surge}` : '—'}
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      )}
    </div>
  );
}

export default RiskTable;
