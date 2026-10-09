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

/**
 * Dashboard — main overview page.
 *
 * Data sources:
 *   GET /weather/current    → current conditions KPIs
 *   GET /weather/history    → 7-day weather chart
 *   GET /demand/historical  → 14-day history
 *   GET /demand/forecast    → 7-day forecast (merged with history)
 *   GET /hospitals + risks  → hospital risk table
 *   GET /alerts             → alerts panel (demo until endpoint agreed)
 *
 * Falls back to clearly-labelled demo data when the backend is unavailable.
 */

const RISK_COLORS = {
  low: '#22c55e', medium: '#f59e0b', high: '#ef4444', critical: '#7c3aed',
};
function riskColor(level) { return RISK_COLORS[level] ?? '#94a3b8'; }

function computeSummary(weatherCurrent, hospitals, demandSeries) {
  if (!weatherCurrent && !hospitals.length && !demandSeries.length) return null;

  const forecastRows = demandSeries.filter((r) => r.type === 'forecast');
  const peakRow      = forecastRows.reduce(
    (best, r) => (r.predicted_admissions > (best?.predicted_admissions ?? -Infinity) ? r : best),
    null
  );
  const atRisk = hospitals.filter(
    (h) => h.risk_level === 'high' || h.risk_level === 'critical'
  ).length;
  const avgOcc = hospitals.length
    ? Math.round(hospitals.reduce((s, h) => s + (h.occupancy_pct ?? 0), 0) / hospitals.length)
    : null;

  const worstRisk = hospitals.reduce((worst, h) => {
    const order = { low: 0, medium: 1, high: 2, critical: 3 };
    return (order[h.risk_level] ?? 0) > (order[worst] ?? 0) ? h.risk_level : worst;
  }, 'low');

  return {
    forecastPeakAdmissions: peakRow?.predicted_admissions ?? '—',
    forecastPeakDate:       peakRow?.date ?? '—',
    avgHospitalOccupancy:   avgOcc,
    facilitiesAtHighRisk:   atRisk,
    overallRiskLevel:       worstRisk,
    dataFreshnessMinutes:   0,
  };
}

function Dashboard() {
  const weather     = useApiData(fetchCurrentWeather,    []);
  const weatherHist = useApiData(fetchWeatherHistory,    [7]);
  const demand      = useApiData(fetchCombinedDemandSeries, [14, 7]);
  const hospitals   = useApiData(fetchAllHospitalsWithRisk, []);
  const alerts      = useApiData(fetchAlerts,            []);

  const loading = weather.loading || demand.loading || hospitals.loading;
  const isDemo  = weather.isDemo || demand.isDemo || hospitals.isDemo;
  const firstError = weather.error ?? demand.error ?? hospitals.error ?? null;

  const summary   = useMemo(
    () => computeSummary(weather.data, hospitals.data ?? [], demand.data ?? []),
    [weather.data, hospitals.data, demand.data]
  );
  const splitDate = (demand.data ?? []).find((r) => r.type === 'forecast')?.date ?? null;

  return (
    <div className="page">

      {/* Connection mode banner */}
      <ConnectionBanner
        isDemo={isDemo}
        error={firstError}
        onRetry={() => {
          weather.refetch(); weatherHist.refetch();
          demand.refetch(); hospitals.refetch(); alerts.refetch();
        }}
      />

      {/* Status banner */}
      <StatusBanner
        riskLevel={summary?.overallRiskLevel ?? 'medium'}
        message={
          summary
            ? `${summary.facilitiesAtHighRisk} hospital(s) at high/critical risk. ` +
              `Peak forecast: ${summary.forecastPeakAdmissions} admissions on ${summary.forecastPeakDate}.`
            : undefined
        }
        freshness={summary?.dataFreshnessMinutes}
        loading={loading}
      />

      {/* KPI cards */}
      <section className="metric-grid" aria-label="Summary metrics">
        <MetricCard
          title="Forecast Peak Admissions"
          value={summary?.forecastPeakAdmissions ?? '—'}
          unit=" pts"
          description={summary ? `Expected ${summary.forecastPeakDate}` : undefined}
          icon="📈"
          trend="up"
          trendLabel="Increasing"
          accentColor="#8b5cf6"
          loading={loading}
          source={isDemo ? 'DEMO — synthetic data' : 'API'}
        />
        <MetricCard
          title="Avg Hospital Occupancy"
          value={summary?.avgHospitalOccupancy ?? '—'}
          unit="%"
          description="Across all registered facilities"
          icon="🏥"
          accentColor={riskColor(
            (summary?.avgHospitalOccupancy ?? 0) >= 85 ? 'critical'
            : (summary?.avgHospitalOccupancy ?? 0) >= 75 ? 'high'
            : (summary?.avgHospitalOccupancy ?? 0) >= 60 ? 'medium' : 'low'
          )}
          loading={loading}
          source={isDemo ? 'DEMO — synthetic data' : 'API'}
        />
        <MetricCard
          title="Facilities at High Risk"
          value={summary?.facilitiesAtHighRisk ?? '—'}
          description="High or critical capacity"
          icon="⚠️"
          accentColor={(summary?.facilitiesAtHighRisk ?? 0) > 0 ? '#ef4444' : '#22c55e'}
          loading={loading}
          source={isDemo ? 'DEMO — synthetic data' : 'API'}
        />
        <MetricCard
          title="Overall Risk Level"
          value={summary ? summary.overallRiskLevel.toUpperCase() : '—'}
          description="Derived from hospital data"
          icon="🌡️"
          accentColor={riskColor(summary?.overallRiskLevel)}
          loading={loading}
          source={isDemo ? 'DEMO — synthetic data' : 'API'}
        />
        <MetricCard
          title="Temperature"
          value={weather.data?.temp_c ?? '—'}
          unit="°C"
          description="Current observation"
          icon="🌤️"
          loading={weather.loading}
          source={weather.isDemo ? 'DEMO — synthetic data' : 'API'}
        />
        <MetricCard
          title="Heat Index"
          value={weather.data?.heat_index ?? '—'}
          unit="°C"
          description="Apparent temperature"
          icon="🔥"
          trend={(weather.data?.heat_index ?? 0) >= 41 ? 'up' : 'neutral'}
          trendLabel={(weather.data?.heat_index ?? 0) >= 41 ? 'Danger zone' : 'Normal'}
          accentColor={(weather.data?.heat_index ?? 0) >= 41 ? '#ef4444' : '#22c55e'}
          loading={weather.loading}
          source={weather.isDemo ? 'DEMO — synthetic data' : 'API'}
        />
        <MetricCard
          title="Humidity"
          value={weather.data?.humidity_pct ?? '—'}
          unit="%"
          icon="💧"
          loading={weather.loading}
          source={weather.isDemo ? 'DEMO — synthetic data' : 'API'}
        />
      </section>

      {/* Demand chart + alerts panel */}
      <div className="dashboard-main-row">
        <div className="dashboard-main-row__chart">
          <DemandChart
            data={demand.data ?? []}
            xKey="date"
            lines={[
              { key: 'admissions', color: '#3b82f6', label: 'Admissions (historical)' },
              { key: 'er_visits',  color: '#ef4444', label: 'ER Visits (historical)'  },
            ]}
            forecastKey="predicted_admissions"
            upperKey="upper_ci"
            lowerKey="lower_ci"
            splitDate={splitDate}
            title={`14-Day History + 7-Day Forecast${isDemo ? ' (Demo)' : ''}`}
            loading={demand.loading}
            error={!demand.isDemo && !!demand.error}
          />
        </div>
        <div className="dashboard-main-row__alerts">
          <AlertsPanel
            alerts={alerts.data ?? []}
            loading={alerts.loading}
            error={!alerts.isDemo && !!alerts.error}
          />
        </div>
      </div>

      {/* Weather chart */}
      <WeatherChart
        data={weatherHist.data ?? []}
        loading={weatherHist.loading}
        error={!weatherHist.isDemo && !!weatherHist.error}
      />

      {/* Hospital risk table */}
      <RiskTable
        rows={hospitals.data ?? []}
        loading={hospitals.loading}
        error={!hospitals.isDemo && !!hospitals.error}
      />
    </div>
  );
}

export default Dashboard;
