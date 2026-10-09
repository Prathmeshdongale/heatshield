import React from 'react';
import {
  ResponsiveContainer, ComposedChart, Line, Area, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';

import MetricCard        from '../components/MetricCard.jsx';
import WeatherChart      from '../components/WeatherChart.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }                          from '../api/useApiData.js';
import { fetchCurrentWeather, fetchWeatherHistory } from '../api/weatherService.js';
import { fetchHistoricalDemand }               from '../api/forecastService.js';

import { HEAT_CATEGORIES, classifyHeatIndex }  from '../data/demoPages.js';

/**
 * HeatwaveAnalysis page
 *
 * Endpoints used:
 *   GET /weather/current         — current conditions KPIs + status banner
 *   GET /weather/history?days=30 — overlay chart (weather side)
 *   GET /demand/historical?days=30 — overlay chart (admissions side)
 *
 * Falls back to demo data when the backend is unavailable.
 * Heat index thresholds are illustrative only — not public-health guidance.
 */

function OverlayChart({ data, isDemo }) {
  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip__label">{label}</p>
        {payload.map((e) => (
          e.value != null && (
            <p key={e.name} style={{ color: e.color }}>
              {e.name}: <strong>{e.value}</strong>
            </p>
          )
        ))}
        {isDemo && <p className="chart-tooltip__demo">⚠ Demo data only</p>}
      </div>
    );
  }

  return (
    <section className="chart-container" aria-label="Heat index vs hospital admissions">
      <div className="chart-header">
        <h2 className="chart-title">
          30-Day Heat Index vs Hospital Admissions{isDemo ? ' (Demo)' : ''}
        </h2>
        {isDemo && <span className="demo-badge">DEMO DATA</span>}
      </div>
      {isDemo && (
        <p className="chart-note">
          Synthetic data illustrating a plausible correlation. Not real observations.
        </p>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 8, right: 40, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={4} />
          <YAxis yAxisId="left"  tick={{ fontSize: 10 }} orientation="left" />
          <YAxis yAxisId="right" tick={{ fontSize: 10 }} orientation="right" domain={[20, 60]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar      yAxisId="left"  dataKey="admissions" fill="#93c5fd" fillOpacity={0.6}  name="Admissions" />
          <Area     yAxisId="right" type="monotone" dataKey="heat_index" stroke="#ef4444" fill="#fecaca" fillOpacity={0.3} name="Heat Index (°C)" dot={false} strokeWidth={2} />
          <Line     yAxisId="right" type="monotone" dataKey="temp_c"     stroke="#f97316" name="Temp (°C)" dot={false} strokeWidth={1.5} strokeDasharray="4 2" />
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
  const demandHist  = useApiData(fetchHistoricalDemand, [30]);

  const isDemo     = weatherNow.isDemo || weatherHist.isDemo || demandHist.isDemo;
  const firstError = weatherNow.error ?? weatherHist.error ?? demandHist.error ?? null;

  const w   = weatherNow.data;
  const cat = classifyHeatIndex(w?.heat_index);

  // Merge weather history + demand history on date for the overlay chart
  const overlayData = (() => {
    const weatherMap = {};
    (weatherHist.data ?? []).forEach((row) => { weatherMap[row.date] = row; });
    return (demandHist.data ?? []).map((row) => ({
      date:        row.date,
      admissions:  row.admissions,
      temp_c:      weatherMap[row.date]?.temp_c ?? null,
      heat_index:  weatherMap[row.date]?.heat_index ?? null,
    })).filter((r) => r.temp_c != null || r.heat_index != null || r.admissions != null);
  })();

  const last7Weather = (weatherHist.data ?? []).slice(-7);
  const loading      = weatherNow.loading || weatherHist.loading || demandHist.loading;

  return (
    <div className="page">
      <ConnectionBanner isDemo={isDemo} error={firstError} onRetry={() => {
        weatherNow.refetch(); weatherHist.refetch(); demandHist.refetch();
      }} />

      <PageHeader
        title="Heatwave Analysis"
        description={
          isDemo
            ? '⚠ Showing synthetic demo data. Weather and demand correlation is illustrative only.'
            : 'Live weather conditions and their relationship to hospital demand.'
        }
        badge={isDemo ? 'DEMO DATA' : null}
      />

      {/* Status banner */}
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
            {isDemo && <span className="demo-badge">DEMO DATA</span>}
          </div>
        </div>
      )}

      {/* Current conditions */}
      <section className="metric-grid" aria-label="Current weather conditions">
        <MetricCard title="Temperature"  value={w?.temp_c       ?? '—'} unit="°C"    icon="🌤️" accentColor="#f97316" loading={weatherNow.loading} source={weatherNow.isDemo ? 'DEMO' : 'API'} />
        <MetricCard title="Heat Index"   value={w?.heat_index   ?? '—'} unit="°C"    description={cat.label} icon="🔥" trend={(w?.heat_index ?? 0) >= 41 ? 'up' : 'neutral'} trendLabel={cat.label} accentColor={cat.color} loading={weatherNow.loading} source={weatherNow.isDemo ? 'DEMO' : 'API'} />
        <MetricCard title="Humidity"     value={w?.humidity_pct ?? '—'} unit="%"     icon="💧" loading={weatherNow.loading} source={weatherNow.isDemo ? 'DEMO' : 'API'} />
      </section>

      {/* Overlay chart */}
      <OverlayChart data={overlayData} isDemo={isDemo} />

      {/* 7-day weather trend */}
      <WeatherChart data={last7Weather} loading={weatherHist.loading} error={!weatherHist.isDemo && !!weatherHist.error} />

      {/* Category table */}
      <HeatCategoryTable currentHeatIndex={w?.heat_index ?? null} />

      {/* Disclaimer */}
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
