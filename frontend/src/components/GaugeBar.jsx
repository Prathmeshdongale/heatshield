import React from 'react';

/**
 * GaugeBar — horizontal percentage gauge with threshold colouring.
 *
 * Props:
 *   value     {number}  — 0–100
 *   label     {string}  — text above bar
 *   showValue {boolean} — show % value (default true)
 *   height    {number}  — bar height in px (default 14)
 */

function getColor(value) {
  if (value >= 90) return '#7c3aed';
  if (value >= 75) return '#ef4444';
  if (value >= 60) return '#f59e0b';
  return '#22c55e';
}

function GaugeBar({ value, label, showValue = true, height = 14 }) {
  const clamped = Math.min(100, Math.max(0, value ?? 0));
  const color   = getColor(clamped);

  return (
    <div className="gauge-bar">
      {label && (
        <div className="gauge-bar__meta">
          <span className="gauge-bar__label">{label}</span>
          {showValue && (
            <span className="gauge-bar__value" style={{ color }}>
              {clamped}%
            </span>
          )}
        </div>
      )}
      <div
        className="gauge-bar__track"
        style={{ height }}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ? `${label}: ${clamped}%` : `${clamped}%`}
      >
        <div
          className="gauge-bar__fill"
          style={{ width: `${clamped}%`, backgroundColor: color, height }}
        />
      </div>
    </div>
  );
}

export default GaugeBar;
