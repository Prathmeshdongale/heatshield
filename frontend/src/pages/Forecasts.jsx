import React, { useState, useEffect, useRef } from 'react';
import DemandChart       from '../components/DemandChart.jsx';
import MetricCard        from '../components/MetricCard.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { fetchDemandForecast } from '../api/forecastService.js';
import { fetchHospitals }      from '../api/hospitalService.js';
import { useApiData }          from '../api/useApiData.js';

const HORIZONS = [
  { value: 7,  label: '7 days'  },
  { value: 14, label: '14 days' },
];

function ForecastDetailTable({ rows }) {
  const forecastRows = (rows ?? []).filter((r) => r.type === 'forecast');
  if (!forecastRows.length) return null;

  return (
    <section aria-label="Forecast detail table">
      <div className="risk-table-header">
        <h2 className="chart-title" style={{ margin: 0 }}>Forecast Detail</h2>
      </div>
      <div className="risk-table-wrapper" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
        <table className="risk-table">
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Predicted Admissions</th>
              <th scope="col">Lower CI</th>
              <th scope="col">Upper CI</th>
              <th scope="col">Risk</th>
            </tr>
          </thead>
          <tbody>
            {forecastRows.map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td><strong>{row.predicted_admissions}</strong></td>
                <td className="text-muted">{row.lower_ci ?? '—'}</td>
                <td className="text-muted">{row.upper_ci ?? '—'}</td>
                <td>
                  <span className="risk-badge" style={{
                    backgroundColor:
                      row.risk_status === 'critical' ? '#7c3aed'
                      : row.risk_status === 'red'    ? '#ef4444'
                      : row.risk_status === 'amber'  ? '#f59e0b'
                      : '#22c55e',
                  }}>
                    {(row.risk_status ?? '—').toUpperCase()}
                  </span>
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

  const hospitalsResult = useApiData(fetchHospitals, []);

  const [forecastState, setForecastState] = useState({ data: null, loading: true, error: null });
  const horizonRef = useRef(horizon);
  horizonRef.current = horizon;

  useEffect(() => {
    setForecastState((s) => ({ ...s, loading: true, error: null }));
    fetchDemandForecast(horizonRef.current).then((result) => {
      setForecastState({ data: result.data, loading: false, error: result.error });
    });
  }, [horizon]);

  const forecastRows = forecastState.data ?? [];
  const splitDate    = forecastRows[0]?.date ?? null;
  const loading      = forecastState.loading;

  const peakRow = forecastRows.reduce(
    (best, r) => (r.predicted_admissions > (best?.predicted_admissions ?? -Infinity) ? r : best),
    null
  );
  const avgForecast = forecastRows.length
    ? Math.round(forecastRows.reduce((s, r) => s + (r.predicted_admissions ?? 0), 0) / forecastRows.length)
    : null;

  return (
    <div className="page">

      <ConnectionBanner
        error={forecastState.error}
        onRetry={() => fetchDemandForecast(horizonRef.current).then((r) =>
          setForecastState({ data: r.data, loading: false, error: r.error })
        )}
      />

      <PageHeader
        title="Demand Forecasts"
        description="Demand projections from Supabase. Not for clinical use."
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

      <section className="metric-grid" aria-label="Forecast summary metrics">
        <MetricCard title="Forecast Horizon"   value={horizon}   unit=" days"        icon="📅" accentColor="#8b5cf6" loading={loading} source="Supabase" />
        <MetricCard title="Peak Predicted"     value={peakRow?.predicted_admissions ?? '—'} unit=" admissions"
          description={peakRow ? `Expected on ${peakRow.date}` : undefined}
          icon="📈" trend="up" trendLabel="Peak day" accentColor="#ef4444" loading={loading} source="Supabase" />
        <MetricCard title="Avg Forecast"       value={avgForecast ?? '—'} unit=" /day"
          description={`Over ${horizon} days`} icon="🔮" loading={loading} source="Supabase" />
      </section>

      <DemandChart
        data={forecastRows}
        xKey="date"
        lines={[]}
        forecastKey="predicted_admissions"
        upperKey="upper_ci"
        lowerKey="lower_ci"
        splitDate={splitDate}
        title={`${horizon}-Day Demand Forecast`}
        loading={loading}
        error={!!forecastState.error}
      />

      <div className="info-box" role="note">
        <p>
          Forecasts are served from Supabase. Confidence intervals reflect model uncertainty
          and widen with forecast horizon. These projections are indicative and not for clinical use.
        </p>
      </div>

      <ForecastDetailTable rows={forecastRows} />
    </div>
  );
}

export default Forecasts;
