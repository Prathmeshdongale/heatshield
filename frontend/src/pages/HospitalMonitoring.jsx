import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';

import MetricCard        from '../components/MetricCard.jsx';
import RiskTable         from '../components/RiskTable.jsx';
import GaugeBar          from '../components/GaugeBar.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }                 from '../api/useApiData.js';
import { fetchAllHospitalsWithRisk, fetchHospitalRisk } from '../api/hospitalService.js';
import { makeOccupancyTrend, DEMO_HOSPITAL_DETAILS } from '../data/demoPages.js';

/**
 * HospitalMonitoring page
 *
 * Endpoints used:
 *   GET /hospitals             — list panel
 *   GET /hospitals/{id}/risk   — detail panel (re-fetched on selection change)
 *
 * Falls back to demo data when the backend is unavailable.
 */

const RISK_META = {
  low:      { color: '#22c55e', label: 'Low'      },
  medium:   { color: '#f59e0b', label: 'Medium'   },
  high:     { color: '#ef4444', label: 'High'     },
  critical: { color: '#7c3aed', label: 'Critical' },
};

function timeAgo(isoString) {
  if (!isoString) return 'unknown';
  const mins = Math.floor((Date.now() - new Date(isoString).getTime()) / 60_000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins} min ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

function HospitalCard({ hospital, selected, onClick }) {
  const meta = RISK_META[hospital.risk_level] ?? RISK_META.low;
  return (
    <button
      className={`hospital-card${selected ? ' hospital-card--selected' : ''}`}
      onClick={() => onClick(hospital.hospital_id)}
      aria-pressed={selected}
      aria-label={`${hospital.name}, risk: ${meta.label}`}
      style={{ borderLeftColor: meta.color }}
    >
      <div className="hospital-card__top">
        <span className="hospital-card__name">{hospital.name}</span>
        <span className="risk-badge" style={{ backgroundColor: meta.color }}>
          {meta.label.toUpperCase()}
        </span>
      </div>
      <div className="hospital-card__sub">
        <span>{hospital.region}</span>
        <span>{hospital.occupancy_pct != null ? `${hospital.occupancy_pct}% occupied` : '—'}</span>
      </div>
    </button>
  );
}

function OccupancyChart({ data, isDemo }) {
  return (
    <section className="chart-container" aria-label="24-hour occupancy trend">
      <div className="chart-header">
        <h2 className="chart-title">24-Hour Occupancy Trend</h2>
        {isDemo && <span className="demo-badge">DEMO DATA</span>}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="hour" tick={{ fontSize: 10 }} interval={3} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
          <Tooltip formatter={(v, name) => [`${v}%`, name]} />
          <Legend />
          <Line type="monotone" dataKey="general_pct" stroke="#3b82f6" name="General (%)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="icu_pct"     stroke="#ef4444" name="ICU (%)"     dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

function HospitalDetail({ hospital, riskData, isDemo }) {
  // 24h trend is always demo — no endpoint in contract
  const trendData = useMemo(
    () => makeOccupancyTrend(hospital.hospital_id),
    [hospital.hospital_id]
  );
  const meta = RISK_META[riskData?.risk_level ?? hospital.risk_level] ?? RISK_META.low;

  // Merge list data with risk data
  const merged = { ...hospital, ...(riskData ?? {}) };
  const availableBeds    = merged.total_beds != null && merged.occupancy_pct != null
    ? Math.round(merged.total_beds * (1 - merged.occupancy_pct / 100)) : '—';
  const availableIcuBeds = merged.icu_beds != null && merged.icu_occupancy_pct != null
    ? Math.round(merged.icu_beds * (1 - merged.icu_occupancy_pct / 100)) : '—';

  const demoBed = DEMO_HOSPITAL_DETAILS[hospital.hospital_id];
  const source  = isDemo ? 'DEMO — synthetic data' : 'API';

  return (
    <div className="hospital-detail">
      <div className="hospital-detail__status" style={{ borderLeftColor: meta.color }}>
        <div>
          <h2 className="hospital-detail__name">{hospital.name}</h2>
          <p className="hospital-detail__address">
            {demoBed?.address ?? hospital.region ?? ''}
          </p>
        </div>
        <div className="hospital-detail__status-right">
          <span className="hospital-detail__risk-pill" style={{ backgroundColor: meta.color }}>
            {meta.label.toUpperCase()} RISK
          </span>
          <span className="hospital-detail__freshness">
            🕐 Updated {timeAgo(merged.last_updated ?? riskData?.date)}
          </span>
          {isDemo && <span className="demo-badge">DEMO DATA</span>}
        </div>
      </div>

      <section className="metric-grid" aria-label="Capacity summary">
        <MetricCard title="General Beds"   value={merged.total_beds ?? '—'} description={`${availableBeds} available`} icon="🛏️" accentColor="#3b82f6" source={source} />
        <MetricCard title="ICU Beds"       value={merged.icu_beds   ?? '—'} description={`${availableIcuBeds} available`} icon="🏥"
          accentColor={(merged.icu_occupancy_pct ?? demoBed?.icu_occupancy_pct ?? 0) >= 80 ? '#ef4444' : '#22c55e'}
          source={source}
        />
        <MetricCard title="Predicted Surge" value={merged.predicted_surge != null ? `+${merged.predicted_surge}` : '—'} unit=" pts"
          description="Over next 24 hours" icon="📈"
          trend={(merged.predicted_surge ?? 0) >= 10 ? 'up' : 'neutral'}
          trendLabel={(merged.predicted_surge ?? 0) >= 10 ? 'High surge' : 'Moderate'}
          accentColor={(merged.predicted_surge ?? 0) >= 15 ? '#7c3aed' : (merged.predicted_surge ?? 0) >= 10 ? '#ef4444' : '#f59e0b'}
          source={source}
        />
      </section>

      <section className="gauge-section" aria-label="Occupancy gauges">
        <div className="chart-header">
          <h2 className="chart-title">Current Occupancy</h2>
          {isDemo && <span className="demo-badge">DEMO DATA</span>}
        </div>
        <div className="gauge-grid">
          <GaugeBar value={merged.occupancy_pct     ?? demoBed?.occupancy_pct}     label="General Ward" />
          <GaugeBar value={merged.icu_occupancy_pct ?? demoBed?.icu_occupancy_pct} label="ICU"          />
          <GaugeBar value={merged.ed_occupancy_pct  ?? demoBed?.ed_occupancy_pct}  label="Emergency Dept" />
        </div>
      </section>

      <OccupancyChart data={trendData} isDemo={true} />
    </div>
  );
}

function HospitalMonitoring() {
  const [selectedId, setSelectedId] = useState(null);

  const allResult  = useApiData(fetchAllHospitalsWithRisk, []);
  const hospitals  = allResult.data ?? [];
  const firstId    = hospitals[0]?.hospital_id ?? null;
  const activeId   = selectedId ?? firstId;

  // Individual risk for selected hospital
  const riskResult = useApiData(
    fetchHospitalRisk,
    [activeId],
    { enabled: !!activeId }
  );

  const selectedHospital = hospitals.find((h) => h.hospital_id === activeId);

  return (
    <div className="page">
      <ConnectionBanner
        isDemo={allResult.isDemo}
        error={allResult.error}
        onRetry={allResult.refetch}
      />

      <PageHeader
        title="Hospital Monitoring"
        description={
          allResult.isDemo
            ? '⚠ Showing synthetic demo data. All values are illustrative.'
            : 'Live capacity and risk data from the connected backend.'
        }
        badge={allResult.isDemo ? 'DEMO DATA' : null}
      />

      <div className="hospital-monitor-layout">
        <aside className="hospital-list-panel" aria-label="Hospital list">
          <p className="hospital-list-panel__title">Select Facility</p>
          <div className="hospital-list">
            {allResult.loading
              ? <p className="table-state">Loading hospitals…</p>
              : hospitals.map((h) => (
                  <HospitalCard
                    key={h.hospital_id}
                    hospital={h}
                    selected={h.hospital_id === activeId}
                    onClick={setSelectedId}
                  />
                ))
            }
          </div>
          <div className="hospital-list-table-wrap">
            <RiskTable rows={hospitals} loading={allResult.loading} error={!allResult.isDemo && !!allResult.error} />
          </div>
        </aside>

        <main className="hospital-detail-panel" aria-label="Hospital detail">
          {allResult.loading
            ? <p className="table-state">Loading…</p>
            : !selectedHospital
              ? <p className="table-state">Select a hospital to view details.</p>
              : <HospitalDetail
                  hospital={selectedHospital}
                  riskData={riskResult.data}
                  isDemo={allResult.isDemo || riskResult.isDemo}
                />
          }
        </main>
      </div>
    </div>
  );
}

export default HospitalMonitoring;
