import React, { useState, useEffect, useRef } from 'react';
import DemandChart       from '../components/DemandChart.jsx';
import MetricCard        from '../components/MetricCard.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { fetchDemandForecast }  from '../api/forecastService.js';
import { fetchHospitals }       from '../api/hospitalService.js';
import { useApiData }           from '../api/useApiData.js';

const HORIZONS = [
  { value: 7,  label: '7 days'  },
  { value: 14, label: '14 days' },
];

function RiskBadge({ status }) {
  const colors = {
    green: '#22c55e', amber: '#f59e0b', red: '#ef4444', critical: '#7c3aed',
    low: '#22c55e', medium: '#f59e0b', high: '#ef4444',
  };
  const color = colors[status] ?? '#94a3b8';
  return (
    <span className="risk-badge" style={{ backgroundColor: color }}>
      {(status ?? '—').toUpperCase()}
    </span>
  );
}

function ForecastDetailTable({ rows }) {
  if (!rows?.length) return null;
  return (
    <section aria-label="Forecast detail table">
      <div className="risk-table-header">
        <h2 className="chart-title" style={{ margin: 0 }}>Forecast Detail — ML Predictions</h2>
      </div>
      <div className="risk-table-wrapper" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
        <table className="risk-table">
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Predicted A&amp;E Visits</th>
              <th scope="col">Lower CI (85%)</th>
              <th scope="col">Upper CI (115%)</th>
              <th scope="col">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td><strong>{row.predicted_admissions}</strong></td>
                <td className="text-muted">{row.lower_ci ?? '—'}</td>
                <td className="text-muted">{row.upper_ci ?? '—'}</td>
                <td><RiskBadge status={row.risk_status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Forecasts() {
  const [horizon,    setHorizon]    = useState(7);
  const [hospitalId, setHospitalId] = useState('H001');

  const hospitalsResult = useApiData(fetchHospitals, []);

  const [forecastState, setForecastState] = useState({ data: null, loading: true, error: null });
  const paramsRef = useRef({ horizon, hospitalId });
  paramsRef.current = { horizon, hospitalId };

  const runForecast = () => {
    const { horizon: h, hospitalId: hid } = paramsRef.current;
    setForecastState((s) => ({ ...s, loading: true, error: null }));
    fetchDemandForecast(h, hid).then((result) => {
      setForecastState({ data: result.data, loading: false, error: result.error });
    });
  };

  useEffect(() => { runForecast(); }, [horizon, hospitalId]);

  const forecastRows = forecastState.data ?? [];
  const splitDate    = forecastRows[0]?.date ?? null;
  const loading      = forecastState.loading;

  const peakRow = forecastRows.reduce(
    (best, r) => ((r.predicted_admissions ?? 0) > (best?.predicted_admissions ?? -Infinity) ? r : best),
    null
  );
  const avgForecast = forecastRows.length
    ? Math.round(forecastRows.reduce((s, r) => s + (r.predicted_admissions ?? 0), 0) / forecastRows.length)
    : null;
  const minForecast = forecastRows.length
    ? Math.round(Math.min(...forecastRows.map((r) => r.predicted_admissions ?? 0)))
    : null;

  const selectedHospital = (hospitalsResult.data ?? []).find((h) => h.hospital_id === hospitalId);

  return (
    <div className="page">
      <ConnectionBanner error={forecastState.error} onRetry={runForecast} />

      <PageHeader
        title="Demand Forecasts"
        description="Real-time A&E attendance predictions from the trained GradientBoosting model (v1.0.0, R²=0.83)."
        actions={
          <div className="page-controls" style={{ display: 'flex', gap: 12 }}>
            <div>
              <label htmlFor="hospital-select" className="control-label">Hospital</label>
              <select
                id="hospital-select"
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
            <div>
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
          </div>
        }
      />

      {/* Hospital context card */}
      {selectedHospital && (
        <div className="info-box" style={{ marginBottom: 0 }}>
          <p>
            <strong>{selectedHospital.name}</strong> — {selectedHospital.region} &nbsp;|&nbsp;
            {selectedHospital.total_beds} beds &nbsp;|&nbsp;
            Occupancy: <strong>{selectedHospital.occupancy_pct}%</strong> &nbsp;|&nbsp;
            Risk: <strong>{(selectedHospital.risk_level ?? selectedHospital.risk_status ?? '—').toUpperCase()}</strong>
          </p>
        </div>
      )}

      {/* KPI cards */}
      <section className="metric-grid" aria-label="Forecast summary metrics">
        <MetricCard title="Forecast Horizon"
          value={horizon} unit=" days"
          icon="📅" accentColor="#8b5cf6" loading={loading} source="ML Model" />
        <MetricCard title="Peak Predicted"
          value={peakRow?.predicted_admissions ?? '—'} unit=" visits"
          description={peakRow ? `Expected on ${peakRow.date}` : undefined}
          icon="📈" trend="up" trendLabel="Peak day" accentColor="#ef4444"
          loading={loading} source="ML Model" />
        <MetricCard title="Avg Forecast"
          value={avgForecast ?? '—'} unit=" visits/day"
          description={`Over ${horizon} days`}
          icon="🔮" loading={loading} source="ML Model" />
        <MetricCard title="Min Forecast"
          value={minForecast ?? '—'} unit=" visits/day"
          description="Lowest predicted day"
          icon="📉" accentColor="#22c55e" loading={loading} source="ML Model" />
      </section>

      {/* Chart */}
      <DemandChart
        data={forecastRows}
        xKey="date"
        lines={[]}
        forecastKey="predicted_admissions"
        upperKey="upper_ci"
        lowerKey="lower_ci"
        splitDate={splitDate}
        title={`${horizon}-Day A&E Forecast — ${selectedHospital?.name ?? hospitalId}`}
        loading={loading}
        error={!!forecastState.error}
      />

      <div className="info-box" role="note">
        <p>
          Predictions from <strong>GradientBoostingRegressor v1.0.0</strong> trained on
          22,825 NHS records. Confidence intervals are ±15% of the point estimate.
          These projections are indicative and <strong>not for clinical use</strong>.
        </p>
      </div>

      <ForecastDetailTable rows={forecastRows} />
    </div>
  );
}

export default Forecasts;
