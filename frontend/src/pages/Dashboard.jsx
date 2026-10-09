import React, { useMemo } from 'react';

import MetricCard        from '../components/MetricCard.jsx';
import DemandChart       from '../components/DemandChart.jsx';
import WeatherChart      from '../components/WeatherChart.jsx';
import RiskTable         from '../components/RiskTable.jsx';
import AlertsPanel       from '../components/AlertsPanel.jsx';
import StatusBanner      from '../components/StatusBanner.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }                from '../api/useApiData.js';
import { fetchCurrentWeather, fetchWeatherHistory } from '../api/weatherService.js';
import { fetchCombinedDemandSeries } from '../api/forecastService.js';
import { fetchAllHospitalsWithRisk } from '../api/hospitalService.js';
import { fetchAlerts }               from '../api/alertsService.js';

const RISK_COLORS = {
  low: '#22c55e', medium: '#f59e0b', high: '#ef4444', critical: '#7c3aed',
  green: '#22c55e', amber: '#f59e0b', red: '#ef4444',
};
function riskColor(level) { return RISK_COLORS[level] ?? '#94a3b8'; }

function computeSummary(weatherCurrent, hospitals, demandSeries) {
  const forecastRows = (demandSeries ?? []).filter((r) => r.type === 'forecast');
  const peakRow = forecastRows.reduce(
    (best, r) => ((r.predicted_admissions ?? 0) > (best?.predicted_admissions ?? -Infinity) ? r : best),
    null
  );
  const atRisk = (hospitals ?? []).filter(
    (h) => h.risk_level === 'high' || h.risk_level === 'critical'
  ).length;
  const avgOcc = (hospitals ?? []).length
    ? Math.round((hospitals ?? []).reduce((s, h) => s + (h.occupancy_pct ?? 0), 0) / hospitals.length)
    : null;
  const worstRisk = (hospitals ?? []).reduce((worst, h) => {
    const order = { low: 0, medium: 1, high: 2, critical: 3 };
    return (order[h.risk_level] ?? 0) > (order[worst] ?? 0) ? h.risk_level : worst;
  }, 'low');

  return {
    forecastPeakAdmissions: peakRow?.predicted_admissions ?? '—',
    forecastPeakDate:       peakRow?.date ?? '—',
    avgHospitalOccupancy:   avgOcc,
    facilitiesAtHighRisk:   atRisk,
    overallRiskLevel:       worstRisk,
  };
}

function Dashboard() {
  const weather     = useApiData(fetchCurrentWeather,       []);
  const weatherHist = useApiData(fetchWeatherHistory,       [7]);
  const demand      = useApiData(fetchCombinedDemandSeries, [14, 7]);
  const hospitals   = useApiData(fetchAllHospitalsWithRisk, []);
  const alerts      = useApiData(fetchAlerts,               []);

  const loading    = weather.loading || demand.loading || hospitals.loading;
  const firstError = hospitals.error ?? weather.error ?? null;

  const summary   = useMemo(
    () => computeSummary(weather.data, hospitals.data ?? [], demand.data ?? []),
    [weather.data, hospitals.data, demand.data]
  );
  const splitDate = (demand.data ?? []).find((r) => r.type === 'forecast')?.date ?? null;

  return (
    <div className="page">

      <ConnectionBanner
        error={firstError}
        onRetry={() => {
          weather.refetch(); weatherHist.refetch();
          demand.refetch(); hospitals.refetch(); alerts.refetch();
        }}
      />

      <StatusBanner
        riskLevel={summary?.overallRiskLevel ?? 'medium'}
        message={
          summary
            ? `${summary.facilitiesAtHighRisk} hospital(s) at high/critical risk. ` +
              `Peak forecast: ${summary.forecastPeakAdmissions} admissions on ${summary.forecastPeakDate}.`
            : undefined
        }
        loading={loading}
      />

      {/* KPI cards */}
      <section className="metric-grid" aria-label="Summary metrics">
        <MetricCard title="Forecast Peak Admissions"
          value={summary?.forecastPeakAdmissions ?? '—'} unit=" pts"
          description={summary ? `Expected ${summary.forecastPeakDate}` : undefined}
          icon="📈" trend="up" trendLabel="Increasing" accentColor="#8b5cf6"
          loading={loading} source="Supabase" />
        <MetricCard title="Avg Hospital Occupancy"
          value={summary?.avgHospitalOccupancy ?? '—'} unit="%"
          description="Across all registered facilities" icon="🏥"
          accentColor={riskColor(
            (summary?.avgHospitalOccupancy ?? 0) >= 85 ? 'critical'
            : (summary?.avgHospitalOccupancy ?? 0) >= 75 ? 'high'
            : (summary?.avgHospitalOccupancy ?? 0) >= 60 ? 'medium' : 'low'
          )}
          loading={loading} source="Supabase" />
        <MetricCard title="Facilities at High Risk"
          value={summary?.facilitiesAtHighRisk ?? '—'}
          description="High or critical capacity" icon="⚠️"
          accentColor={(summary?.facilitiesAtHighRisk ?? 0) > 0 ? '#ef4444' : '#22c55e'}
          loading={loading} source="Supabase" />
        <MetricCard title="Overall Risk Level"
          value={summary ? summary.overallRiskLevel.toUpperCase() : '—'}
          description="Derived from hospital data" icon="🌡️"
          accentColor={riskColor(summary?.overallRiskLevel)}
          loading={loading} source="Supabase" />
        <MetricCard title="Temperature"
          value={weather.data?.temp_c ?? '—'} unit="°C"
          description="Current observation" icon="🌤️"
          loading={weather.loading} source="Supabase" />
        <MetricCard title="Heat Index"
          value={weather.data?.heat_index ?? '—'} unit="°C"
          description="Apparent temperature" icon="🔥"
          trend={(weather.data?.heat_index ?? 0) >= 41 ? 'up' : 'neutral'}
          trendLabel={(weather.data?.heat_index ?? 0) >= 41 ? 'Danger zone' : 'Normal'}
          accentColor={(weather.data?.heat_index ?? 0) >= 41 ? '#ef4444' : '#22c55e'}
          loading={weather.loading} source="Supabase" />
        <MetricCard title="Humidity"
          value={weather.data?.humidity_pct ?? '—'} unit="%"
          icon="💧" loading={weather.loading} source="Supabase" />
      </section>

      {/* Demand chart + alerts */}
      <div className="dashboard-main-row">
        <div className="dashboard-main-row__chart">
          <DemandChart
            data={demand.data ?? []}
            xKey="date"
            lines={[]}
            forecastKey="predicted_admissions"
            upperKey="upper_ci"
            lowerKey="lower_ci"
            splitDate={splitDate}
            title="7-Day Demand Forecast"
            loading={demand.loading}
            error={!!demand.error}
          />
        </div>
        <div className="dashboard-main-row__alerts">
          <AlertsPanel
            alerts={alerts.data ?? []}
            loading={alerts.loading}
            error={!!alerts.error}
          />
        </div>
      </div>

      <WeatherChart
        data={weatherHist.data ?? []}
        loading={weatherHist.loading}
        error={!!weatherHist.error}
      />

      <RiskTable
        rows={hospitals.data ?? []}
        loading={hospitals.loading}
        error={!!hospitals.error}
      />
    </div>
  );
}

export default Dashboard;
