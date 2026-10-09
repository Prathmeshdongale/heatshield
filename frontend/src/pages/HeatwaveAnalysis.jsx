import React from 'react';
import {
  ResponsiveContainer, ComposedChart, Line, Area, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';

import MetricCard        from '../components/MetricCard.jsx';
import WeatherChart      from '../components/WeatherChart.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }                               from '../api/useApiData.js';
import { fetchCurrentWeather, fetchWeatherHistory } from '../api/weatherService.js';
import { HEAT_CATEGORIES, classifyHeatIndex }       from '../data/demoPages.js';

function OverlayChart({ data }) {
  return (
    <section className="chart-container" aria-label="Heat index vs temperature">
      <div className="chart-header">
        <h2 className="chart-title">Weather History — Heat Index vs Temperature</h2>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 8, right: 40, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={4} />
          <YAxis yAxisId="left"  tick={{ fontSize: 10 }} orientation="left"  domain={[0, 50]} />
          <YAxis yAxisId="right" tick={{ fontSize: 10 }} orientation="right" domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Area yAxisId="left"  type="monotone" dataKey="heat_index" stroke="#ef4444"
            fill="#fecaca" fillOpacity={0.3} name="Heat Index (°C)" dot={false} strokeWidth={2} />
          <Line yAxisId="left"  type="monotone" dataKey="temp_c"     stroke="#f97316"
            name="Temp (°C)" dot={false} strokeWidth={1.5} strokeDasharray="4 2" />
          <Bar  yAxisId="right" dataKey="humidity_pct" fill="#93c5fd" fillOpacity={0.5} name="Humidity (%)" />
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}

function HeatCategoryTable({ currentHeatIndex }) {
  return (
    <section aria-label="Heat index category reference">
      <div className="risk-table-header">
        <h2 className="chart-title" style={{ margin: 0 }}>
          Heat Index Categories
          <span className="chart-note" style={{ fontWeight: 400, marginLeft: 8 }}>
            (illustrative — not official guidance)
          </span>
        </h2>
      </div>
      <div className="risk-table-wrapper" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
        <table className="risk-table">
          <thead>
            <tr>
              <th scope="col">Category</th>
              <th scope="col">Range</th>
              <th scope="col">Description</th>
              <th scope="col">Current</th>
            </tr>
          </thead>
          <tbody>
            {HEAT_CATEGORIES.map((cat) => {
              const isCurrent = currentHeatIndex != null
                && (cat.min == null || currentHeatIndex >= cat.min)
                && (cat.max == null || currentHeatIndex < cat.max);
              const range = cat.min == null ? `< ${cat.max} °C`
                          : cat.max == null ? `≥ ${cat.min} °C`
                          : `${cat.min}–${cat.max} °C`;
              return (
                <tr key={cat.label} className={isCurrent ? 'risk-table__row--current' : ''}>
                  <td><span className="risk-badge" style={{ backgroundColor: cat.color }}>{cat.label.toUpperCase()}</span></td>
                  <td>{range}</td>
                  <td>{cat.description}</td>
                  <td>{isCurrent ? '👈 Current' : ''}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function HeatwaveAnalysis() {
  const weatherNow  = useApiData(fetchCurrentWeather,  []);
  const weatherHist = useApiData(fetchWeatherHistory,  [30]);

  const w     = weatherNow.data;
  const cat   = classifyHeatIndex(w?.heat_index);
  const error = weatherNow.error ?? weatherHist.error ?? null;
  const loading = weatherNow.loading || weatherHist.loading;

  return (
    <div className="page">
      <ConnectionBanner
        error={error}
        onRetry={() => { weatherNow.refetch(); weatherHist.refetch(); }}
      />

      <PageHeader
        title="Heatwave Analysis"
        description="Live weather conditions from Supabase."
      />

      {!loading && w && (
        <div
          className="status-banner"
          style={{ backgroundColor: cat.color + '22', borderColor: cat.color, color: cat.color }}
          role="status"
          aria-live="polite"
        >
          <span className="status-banner__icon" aria-hidden="true">🌡️</span>
          <div className="status-banner__body">
            <strong>{cat.label}</strong>{' — '}{cat.description}
          </div>
          <div className="status-banner__meta">
            <span className="status-banner__freshness">Heat index: {w.heat_index} °C</span>
          </div>
        </div>
      )}

      <section className="metric-grid" aria-label="Current weather conditions">
        <MetricCard title="Temperature"  value={w?.temp_c       ?? '—'} unit="°C"
          icon="🌤️" accentColor="#f97316" loading={weatherNow.loading} source="Supabase" />
        <MetricCard title="Heat Index"   value={w?.heat_index   ?? '—'} unit="°C"
          description={cat.label} icon="🔥"
          trend={(w?.heat_index ?? 0) >= 41 ? 'up' : 'neutral'}
          trendLabel={cat.label} accentColor={cat.color}
          loading={weatherNow.loading} source="Supabase" />
        <MetricCard title="Humidity"     value={w?.humidity_pct ?? '—'} unit="%"
          icon="💧" loading={weatherNow.loading} source="Supabase" />
      </section>

      <OverlayChart data={weatherHist.data ?? []} />

      <WeatherChart data={(weatherHist.data ?? []).slice(-7)}
        loading={weatherHist.loading} error={!!weatherHist.error} />

      <HeatCategoryTable currentHeatIndex={w?.heat_index ?? null} />

      <section className="info-box info-box--warning" role="note">
        <h2 className="section-title">⚠ Important Disclaimer</h2>
        <p>
          The heat index thresholds shown are for UI demonstration purposes only.
          They do not replace guidance from any public-health authority, clinical
          body, or emergency-management service.
        </p>
      </section>
    </div>
  );
}

export default HeatwaveAnalysis;
