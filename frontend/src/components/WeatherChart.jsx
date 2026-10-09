import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

/**
 * WeatherChart — 7-day weather trend area chart.
 * Uses Recharts (same library as DemandChart) for consistency.
 *
 * Props:
 *   data     {Array}   — array of { date, temp_c, heat_index, humidity_pct }
 *   loading  {boolean} — skeleton state
 *   error    {boolean} — error state
 */
function WeatherChart({ data = [], loading = false, error = false }) {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="skeleton skeleton--text-md" style={{ width: 200, marginBottom: 16 }} />
        <div className="chart-skeleton" aria-label="Loading weather chart" aria-busy="true" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-container chart-container--error" role="alert">
        <p className="chart-error">⚠ Weather data could not be loaded.</p>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="chart-placeholder" aria-label="No weather data">
        No weather data available.
      </div>
    );
  }

  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip__label">{label}</p>
        {payload.map((entry) => (
          <p key={entry.name} style={{ color: entry.color }}>
            {entry.name}: <strong>{entry.value}</strong>
          </p>
        ))}
        <p className="chart-tooltip__demo">⚠ Demo data only</p>
      </div>
    );
  }

  return (
    <section className="chart-container" aria-label="7-day weather trend">
      <div className="chart-header">
        <h2 className="chart-title">7-Day Weather Trend</h2>
        <span className="demo-badge">DEMO DATA</span>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gradTemp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#f97316" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="gradHeat" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          <Area
            type="monotone"
            dataKey="temp_c"
            stroke="#f97316"
            fill="url(#gradTemp)"
            name="Temp (°C)"
            dot={false}
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="heat_index"
            stroke="#ef4444"
            fill="url(#gradHeat)"
            name="Heat Index (°C)"
            dot={false}
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="humidity_pct"
            stroke="#3b82f6"
            fill="none"
            name="Humidity (%)"
            dot={false}
            strokeWidth={1.5}
            strokeDasharray="4 2"
          />
        </AreaChart>
      </ResponsiveContainer>
    </section>
  );
}

export default WeatherChart;
