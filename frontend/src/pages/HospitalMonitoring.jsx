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

import { useApiData }                                   from '../api/useApiData.js';
import { fetchAllHospitalsWithRisk, fetchHospitalRisk } from '../api/hospitalService.js';

const RISK_META = {
  low:      { color: '#22c55e', label: 'Low'      },
  medium:   { color: '#f59e0b', label: 'Medium'   },
  high:     { color: '#ef4444', label: 'High'     },
  critical: { color: '#7c3aed', label: 'Critical' },
  green:    { color: '#22c55e', label: 'Low'      },
  amber:    { color: '#f59e0b', label: 'Medium'   },
  red:      { color: '#ef4444', label: 'High'     },
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

function HospitalDetail({ hospital, riskData }) {
  const meta   = RISK_META[riskData?.risk_level ?? hospital.risk_level] ?? RISK_META.low;
  const merged = { ...hospital, ...(riskData ?? {}) };

  const availableBeds = merged.total_beds != null && merged.occupancy_pct != null
    ? Math.round(merged.total_beds * (1 - merged.occupancy_pct / 100)) : '—';

  return (
    <div className="hospital-detail">
      <div className="hospital-detail__status" style={{ borderLeftColor: meta.color }}>
        <div>
          <h2 className="hospital-detail__name">{hospital.name}</h2>
          <p className="hospital-detail__address">{hospital.region ?? ''}</p>
        </div>
        <div className="hospital-detail__status-right">
          <span className="hospital-detail__risk-pill" style={{ backgroundColor: meta.color }}>
            {meta.label.toUpperCase()} RISK
          </span>
          <span className="hospital-detail__freshness">
            🕐 Updated {timeAgo(merged.last_updated ?? riskData?.date)}
          </span>
        </div>
      </div>

      <section className="metric-grid" aria-label="Capacity summary">
        <MetricCard title="Total Beds"    value={merged.total_beds ?? '—'}
          description={`${availableBeds} available`} icon="🛏️" accentColor="#3b82f6" source="Supabase" />
        <MetricCard title="Available Beds" value={merged.capacity_available ?? availableBeds}
          icon="✅" accentColor="#22c55e" source="Supabase" />
        <MetricCard title="Occupancy"     value={merged.occupancy_pct ?? '—'} unit="%"
          icon="📊" accentColor={
            (merged.occupancy_pct ?? 0) >= 90 ? '#7c3aed'
            : (merged.occupancy_pct ?? 0) >= 85 ? '#ef4444'
            : (merged.occupancy_pct ?? 0) >= 70 ? '#f59e0b'
            : '#22c55e'
          } source="Supabase" />
      </section>

      <section className="gauge-section" aria-label="Occupancy gauges">
        <div className="chart-header">
          <h2 className="chart-title">Current Occupancy</h2>
        </div>
        <div className="gauge-grid">
          <GaugeBar value={merged.occupancy_pct}     label="General Ward" />
          <GaugeBar value={merged.icu_occupancy_pct} label="ICU" />
          <GaugeBar value={merged.ed_occupancy_pct}  label="Emergency Dept" />
        </div>
      </section>
    </div>
  );
}

function HospitalMonitoring() {
  const [selectedId, setSelectedId] = useState(null);

  const allResult = useApiData(fetchAllHospitalsWithRisk, []);
  const hospitals = allResult.data ?? [];
  const firstId   = hospitals[0]?.hospital_id ?? null;
  const activeId  = selectedId ?? firstId;

  const riskResult = useApiData(fetchHospitalRisk, [activeId], { enabled: !!activeId });
  const selectedHospital = hospitals.find((h) => h.hospital_id === activeId);

  return (
    <div className="page">
      <ConnectionBanner error={allResult.error} onRetry={allResult.refetch} />

      <PageHeader
        title="Hospital Monitoring"
        description="Live capacity and risk data from Supabase."
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
            <RiskTable rows={hospitals} loading={allResult.loading} error={!!allResult.error} />
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
                />
          }
        </main>
      </div>
    </div>
  );
}

export default HospitalMonitoring;
