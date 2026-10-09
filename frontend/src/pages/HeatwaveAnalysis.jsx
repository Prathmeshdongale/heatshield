import React, { useState } from 'react';
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
import { fetchHospitals }                           from '../api/hospitalService.js';
import { HEAT_CATEGORIES, classifyHeatIndex }       from '../data/demoPages.js';

// ── Sub-components ─────────────────────────────────────────────────────────

function OverlayChart({ data, location }) {
  if (!data?.length) return null;
  return (
    <section className="chart-container" aria-label="Heat index vs temperature history">
      <div className="chart-header">
        <h2 className="chart-title">30-Day Weather History — {location}</h2>
        <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 400 }}>
          Source: Open-Meteo
        </span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 8, right: 40, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={Math.floor(data.length / 6)} />
          <YAxis yAxisId="left"  tick={{ fontSize: 10 }} orientation="left"  domain={['auto', 'auto']} />
          <YAxis yAxisId="right" tick={{ fontSize: 10 }} orientation="right" domain={[0, 100]} />
          <Tooltip
            formatter={(value, name) => [
              name === 'Humidity (%)' ? `${value}%` : `${value} °C`,
              name,
            ]}
          />
          <Legend />
          <Area yAxisId="left" type="monotone" dataKey="heat_index"
            stroke="#ef4444" fill="#fecaca" fillOpacity={0.3}
            name="Heat Index (°C)" dot={false} strokeWidth={2} />
          <Line yAxisId="left" type="monotone" dataKey="temp_c"
            stroke="#f97316" name="Temp Max (°C)" dot={false}
            strokeWidth={1.5} strokeDasharray="4 2" />
          <Bar yAxisId="right" dataKey="humidity_pct"
            fill="#93c5fd" fillOpacity={0.5} name="Humidity (%)" />
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
                  <td>
                    <span className="risk-badge" style={{ backgroundColor: cat.color }}>
                      {cat.label.toUpperCase()}
                    </span>
                  </td>
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

// ── Page ───────────────────────────────────────────────────────────────────

function HeatwaveAnalysis() {
  const [hospitalId, setHospitalId] = useState('H001');

  // Fetch hospital list for selector
  const hospitalsResult = useApiData(fetchHospitals, []);

  // Current conditions (today) — for KPI cards
  const weatherNow  = useApiData(fetchCurrentWeather,  [hospitalId], { enabled: !!hospitalId });

  // 30-day history for charts
  const weatherHist = useApiData(fetchWeatherHistory,  [30, hospitalId], { enabled: !!hospitalId });

  const w       = weatherNow.data;
  const cat     = classifyHeatIndex(w?.heat_index);
  const error   = weatherNow.error ?? weatherHist.error ?? null;
  const loading = weatherNow.loading || weatherHist.loading;

  const selectedHospital = (hospitalsResult.data ?? []).find((h) => h.hospital_id === hospitalId);
  const locationLabel    = selectedHospital
    ? `${selectedHospital.name} (${selectedHospital.region})`
    : hospitalId;

  // Colour thresholds for current temperature
  const tempAccent = (w?.temp_c ?? 0) >= 35 ? '#ef4444'
    : (w?.temp_c ?? 0) >= 28 ? '#f97316' : '#22c55e';

  return (
    <div className="page">

      <ConnectionBanner
        error={error}
        onRetry={() => { weatherNow.refetch(); weatherHist.refetch(); }}
      />

      <PageHeader
        title="Heatwave Analysis"
        description="Live temperature and humidity from Open-Meteo — updated daily, no API key needed."
        actions={
          <div className="page-controls">
            <label htmlFor="wx-hospital" className="control-label">Location</label>
            <select
              id="wx-hospital"
              className="control-select"
              value={hospitalId}
              onChange={(e) => setHospitalId(e.target.value)}
            >
              {(hospitalsResult.data ?? []).map((h) => (
                <option key={h.hospital_id} value={h.hospital_id}>
                  {h.hospital_id} — {h.name}
                </option>
              ))}
            </select>
          </div>
        }
      />

      {/* Heat-level status banner */}
      {!loading && w && (
        <div
          className="status-banner"
          style={{ backgroundColor: cat.color + '22', borderColor: cat.color, color: cat.color }}
          role="status" aria-live="polite"
        >
          <span className="status-banner__icon" aria-hidden="true">🌡️</span>
          <div className="status-banner__body">
            <strong>{cat.label}</strong>{' — '}{cat.description}
          </div>
          <div className="status-banner__meta">
            <span className="status-banner__freshness">
              Heat index: <strong>{w.heat_index} °C</strong> &nbsp;|&nbsp; {locationLabel}
            </span>
          </div>
        </div>
      )}

      {/* KPI cards — live from Open-Meteo */}
      <section className="metric-grid" aria-label="Current weather conditions">
        <MetricCard
          title="Temperature (Max)"
          value={w?.temp_c ?? '—'} unit="°C"
          description={`Today — ${locationLabel}`}
          icon="🌤️" accentColor={tempAccent}
          loading={weatherNow.loading} source="Open-Meteo" />
        <MetricCard
          title="Heat Index"
          value={w?.heat_index ?? '—'} unit="°C"
          description={`${cat.label} — apparent temperature`}
          icon="🔥"
          trend={(w?.heat_index ?? 0) >= 35 ? 'up' : 'neutral'}
          trendLabel={cat.label}
          accentColor={cat.color}
          loading={weatherNow.loading} source="Open-Meteo" />
        <MetricCard
          title="Humidity"
          value={w?.humidity_pct ?? '—'} unit="%"
          description="Relative humidity"
          icon="💧"
          accentColor={(w?.humidity_pct ?? 0) >= 80 ? '#3b82f6' : '#22c55e'}
          loading={weatherNow.loading} source="Open-Meteo" />
        <MetricCard
          title="7-day Avg Temp"
          value={
            weatherHist.data?.length
              ? Math.round(
                  weatherHist.data.slice(-7).reduce((s, r) => s + (r.temp_c ?? 0), 0) /
                  Math.min(weatherHist.data.length, 7) * 10
                ) / 10
              : '—'
          }
          unit="°C"
          description="Mean over last 7 days"
          icon="📅" accentColor="#8b5cf6"
          loading={weatherHist.loading} source="Open-Meteo" />
      </section>

      {/* 30-day overlay chart */}
      <OverlayChart data={weatherHist.data ?? []} location={locationLabel} />

      {/* 7-day area chart */}
      <WeatherChart
        data={(weatherHist.data ?? []).slice(-7)}
        loading={weatherHist.loading}
        error={!!weatherHist.error}
        location={locationLabel}
      />

      {/* Heat category reference */}
      <HeatCategoryTable currentHeatIndex={w?.heat_index ?? null} />

      {/* Source info */}
      <div className="info-box" role="note">
        <p>
          <strong>Data source:</strong> <a href="https://open-meteo.com" target="_blank" rel="noopener noreferrer">Open-Meteo</a> —
          free, open-source weather API. No API key required. Data updated daily.
          Coordinates: {selectedHospital
            ? `${selectedHospital.name} lat/lon from Supabase`
            : 'Default NHS region coordinates'}.
        </p>
      </div>

      <section className="info-box info-box--warning" role="note">
        <h2 className="section-title">⚠ Important Disclaimer</h2>
        <p>
          Heat index thresholds are for informational purposes only. They do not replace
          guidance from any public-health authority, clinical body, or emergency-management service.
        </p>
      </section>
    </div>
  );
}

export default HeatwaveAnalysis;
