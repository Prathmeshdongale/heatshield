import React, { useState, useEffect, useRef } from 'react';
import DemandChart       from '../components/DemandChart.jsx';
import MetricCard        from '../components/MetricCard.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { fetchHistoricalDemand, fetchDemandForecast } from '../api/forecastService.js';
import { fetchHospitals }                             from '../api/hospitalService.js';
import { useApiData }                                 from '../api/useApiData.js';

/**
 * Forecasts page
 *
 * Endpoints used:
 *   GET /hospitals                   — populate the facility selector
 *   GET /demand/historical?days=14   — history portion of the chart
 *   GET /demand/forecast?days=N      — forecast portion (re-fetched on horizon change)
 *
 * Falls back to demo data when the backend is unavailable.
 */

const HORIZONS = [
  { value: 7,  label: '7 days'  },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
];

function ForecastDetailTable({ rows, isDemo }) {
  const forecastRows = (rows ?? []).filter((r) => r.type === 'forecast');
  if (!forecastRows.length) return null;

  return (
    <section aria-label="Forecast detail table">
      <div className="risk-table-header">
        <h2 className="chart-title" style={{ margin: 0 }}>Forecast Detail</h2>
        {isDemo && <span className="demo-badge">DEMO DATA</span>}
      </div>
      <div className="risk-table-wrapper" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
        <table className="risk-table">
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Predicted Admissions</th>
              <th scope="col">Lower CI</th>
              <th scope="col">Upper CI</th>
              <th scope="col">CI Width</th>
              <th scope="col">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {forecastRows.map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td><strong>{row.predicted_admissions}</strong></td>
                <td className="text-muted">{row.lower_ci ?? '—'}</td>
                <td className="text-muted">{row.upper_ci ?? '—'}</td>
                <td className="text-muted">
                  {row.upper_ci != null && row.lower_ci != null
                    ? row.upper_ci - row.lower_ci : '—'}
                </td>
                <td>
                  {row.confidence != null
                    ? (
                      <span style={{
                        color: row.confidence >= 0.8 ? '#22c55e'
                             : row.confidence >= 0.7 ? '#f59e0b' : '#ef4444',
                        fontWeight: 600,
                      }}>
                        {Math.round(row.confidence * 100)}%
                      </span>
                    )
                    : '—'
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Forecasts() {
  const [horizon, setHorizon] = useState(7);

  // Hospitals list — for the facility selector label (no per-hospital API endpoint in contract)
  const hospitalsResult = useApiData(fetchHospitals, []);

  // History is fixed at 14 days
  const historyResult = useApiData(fetchHistoricalDemand, [14]);

  // Forecast re-fetches when horizon changes
  const [forecastState, setForecastState] = useState({ data: null, loading: true, error: null, isDemo: false });
  const horizonRef = useRef(horizon);
  horizonRef.current = horizon;

  useEffect(() => {
    setForecastState((s) => ({ ...s, loading: true, error: null }));
    fetchDemandForecast(horizonRef.current).then((result) => {
      setForecastState({
        data:    result.data,
        loading: false,
        error:   result.isDemo ? null : result.error,
        isDemo:  result.isDemo,
      });
    });
  }, [horizon]);

  const combined = [
    ...(historyResult.data ?? []),
    ...(forecastState.data ?? []),
  ];

  const splitDate  = combined.find((r) => r.type === 'forecast')?.date ?? null;
  const isDemo     = historyResult.isDemo || forecastState.isDemo;
  const firstError = historyResult.error ?? forecastState.error ?? null;
  const loading    = historyResult.loading || forecastState.loading;

  // Summary stats
  const forecastRows = (forecastState.data ?? []);
  const peakRow = forecastRows.reduce(
    (best, r) => (r.predicted_admissions > (best?.predicted_admissions ?? -Infinity) ? r : best),
    null
  );
  const historyRows = historyResult.data ?? [];
  const avgHist = historyRows.length
    ? Math.round(historyRows.reduce((s, r) => s + (r.admissions ?? 0), 0) / historyRows.length)
    : null;
  const avgForecast = forecastRows.length
    ? Math.round(forecastRows.reduce((s, r) => s + (r.predicted_admissions ?? 0), 0) / forecastRows.length)
    : null;
  const avgConf = forecastRows.length && forecastRows[0]?.confidence != null
    ? Math.round(
        forecastRows.reduce((s, r) => s + (r.confidence ?? 0), 0) / forecastRows.length * 100
      )
    : null;

  const source = isDemo ? 'DEMO — synthetic data' : 'API';

  const facilityOptions = [
    { hospital_id: 'all', name: 'All Hospitals (System-wide)' },
    ...(hospitalsResult.data ?? []),
  ];

  return (
    <div className="page">

      <ConnectionBanner isDemo={isDemo} error={firstError} onRetry={() => {
        historyResult.refetch();
        fetchDemandForecast(horizon).then((r) => setForecastState({
          data: r.data, loading: false, error: r.isDemo ? null : r.error, isDemo: r.isDemo,
        }));
      }} />

      <PageHeader
        title="Demand Forecasts"
        description={
          isDemo
            ? '⚠ Showing synthetic demo data. Connect the backend to see real forecasts.'
            : 'Demand projections from the connected backend. Not for clinical use.'
        }
        badge={isDemo ? 'DEMO DATA' : null}
        actions={
          <div className="page-controls">
            <label htmlFor="horizon-select" className="control-label">Horizon</label>
            <select
              id="horizon-select"
              className="control-select"
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            >
              {HORIZONS.map((h) => (
                <option key={h.value} value={h.value}>{h.label}</option>
              ))}
            </select>
          </div>
        }
      />

      {/* KPI cards */}
      <section className="metric-grid" aria-label="Forecast summary metrics">
        <MetricCard title="Forecast Horizon"     value={horizon}     unit=" days"        icon="📅" accentColor="#8b5cf6" loading={loading} source={source} />
        <MetricCard title="Peak Predicted"        value={peakRow?.predicted_admissions ?? '—'} unit=" admissions" description={peakRow ? `Expected on ${peakRow.date}` : undefined} icon="📈" trend="up" trendLabel="Peak day" accentColor="#ef4444" loading={loading} source={source} />
        <MetricCard title="Avg Historical (14d)"  value={avgHist ?? '—'} unit=" /day"    description="Prior 14 days"                  icon="📊" loading={loading} source={source} />
        <MetricCard title="Avg Forecast"          value={avgForecast ?? '—'} unit=" /day" description={`Over ${horizon} days`}        icon="🔮" loading={loading} source={source} />
        <MetricCard title="Avg Confidence"        value={avgConf ?? '—'} unit="%"        description={avgConf == null ? 'Not provided by API' : 'CI widens with horizon'} icon="🎯"
          accentColor={avgConf == null ? '#94a3b8' : avgConf >= 80 ? '#22c55e' : avgConf >= 70 ? '#f59e0b' : '#ef4444'}
          loading={loading} source={source}
        />
      </section>

      {/* Demand chart */}
      <DemandChart
        data={combined}
        xKey="date"
        lines={[
          { key: 'admissions', color: '#3b82f6', label: 'Admissions (historical)' },
          { key: 'er_visits',  color: '#ef4444', label: 'ER Visits (historical)'  },
        ]}
        forecastKey="predicted_admissions"
        upperKey="upper_ci"
        lowerKey="lower_ci"
        splitDate={splitDate}
        title={`14-Day History + ${horizon}-Day Forecast${isDemo ? ' (Demo)' : ''}`}
        loading={loading}
        error={!isDemo && !!firstError}
      />

      {!isDemo && (
        <div className="info-box" role="note">
          <p>
            Forecasts are served by the connected backend. Confidence intervals
            reflect the model's uncertainty and widen with forecast horizon.
            These projections are indicative and not for clinical use.
          </p>
        </div>
      )}

      {isDemo && (
        <div className="info-box info-box--warning" role="note">
          <p>
            <strong>⚠ Demo data only.</strong> Confidence intervals shown are
            synthetic and widen with horizon to illustrate expected model behaviour.
            These are not real statistical forecasts.
          </p>
        </div>
      )}

      <ForecastDetailTable rows={combined} isDemo={isDemo} />
    </div>
  );
}

export default Forecasts;
