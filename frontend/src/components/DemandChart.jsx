import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

/**
 * DemandChart — combined historical + forecast demand chart.
 *
 * Renders historical admissions as a solid blue line, ER visits as a red
 * line, and forecast admissions with a shaded confidence interval band.
 * A reference line marks the boundary between history and forecast.
 *
 * Props:
 *   data        {Array}   — merged historical + forecast rows
 *   xKey        {string}  — field name for x-axis (default "date")
 *   lines       {Array}   — [{ key, color, label, dashed? }] for simple lines
 *   forecastKey {string}  — field name of the forecast line (draws CI band)
 *   upperKey    {string}  — upper confidence interval field
 *   lowerKey    {string}  — lower confidence interval field
 *   splitDate   {string}  — YYYY-MM-DD where history ends / forecast begins
 *   title       {string}  — accessible chart title
 *   loading     {boolean} — skeleton state
 *   error       {boolean} — error state
 */
function DemandChart({
  data = [],
  xKey = 'date',
  lines = [],
  forecastKey,
  upperKey,
  lowerKey,
  splitDate,
  title = 'Demand Chart',
  loading = false,
  error = false,
}) {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="skeleton skeleton--text-md" style={{ width: 220, marginBottom: 16 }} />
        <div className="chart-skeleton" aria-label="Loading chart" aria-busy="true" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-container chart-container--error" role="alert">
        <p className="chart-error">⚠ Chart data could not be loaded.</p>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="chart-placeholder" aria-label="No chart data available">
        No data available.
      </div>
    );
  }

  // Custom tooltip to show the demo disclaimer
  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip__label">{label}</p>
        {payload.map((entry) => (
          entry.value != null && (
            <p key={entry.name} style={{ color: entry.color }}>
              {entry.name}: <strong>{entry.value}</strong>
            </p>
          )
        ))}
      </div>
    );
  }

  return (
    <section className="chart-container" aria-label={title}>
      <div className="chart-header">
        <h2 className="chart-title">{title}</h2>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={xKey} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Confidence interval band (rendered as area, behind lines) */}
          {upperKey && lowerKey && (
            <Area
              type="monotone"
              dataKey={upperKey}
              stroke="none"
              fill="#c4b5fd"
              fillOpacity={0.25}
              name="Upper CI"
              legendType="none"
              activeDot={false}
              dot={false}
            />
          )}
          {lowerKey && (
            <Area
              type="monotone"
              dataKey={lowerKey}
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
              name="Lower CI"
              legendType="none"
              activeDot={false}
              dot={false}
            />
          )}

          {/* Regular lines */}
          {lines.map(({ key, color, label, dashed }) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              name={label ?? key}
              dot={false}
              strokeWidth={2}
              strokeDasharray={dashed ? '5 3' : undefined}
              connectNulls={false}
            />
          ))}

          {/* Forecast line — real ML predictions */}
          {forecastKey && (
            <Line
              type="monotone"
              dataKey={forecastKey}
              stroke="#8b5cf6"
              name="ML Forecast"
              dot={{ fill: '#8b5cf6', r: 3 }}
              strokeWidth={2.5}
              strokeDasharray="6 3"
              connectNulls={false}
            />
          )}

          {/* History / forecast boundary */}
          {splitDate && (
            <ReferenceLine
              x={splitDate}
              stroke="#94a3b8"
              strokeDasharray="3 3"
              label={{ value: 'Forecast →', position: 'top', fontSize: 10, fill: '#64748b' }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}

export default DemandChart;
