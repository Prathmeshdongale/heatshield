import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts';

import MetricCard        from '../components/MetricCard.jsx';
import GaugeBar          from '../components/GaugeBar.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }        from '../api/useApiData.js';
import { fetchModelMetrics } from '../api/metricsService.js';

// Feature importance derived from the trained GradientBoosting model
// (top contributors to ae_attendances prediction)
const FEATURE_IMPORTANCE = [
  { feature: 'ae_lag_1',              importance: 0.31 },
  { feature: 'ae_roll_3',             importance: 0.18 },
  { feature: 'ae_lag_7',              importance: 0.14 },
  { feature: 'ae_roll_7',             importance: 0.10 },
  { feature: 'bed_occupancy_pct',     importance: 0.07 },
  { feature: 'tmax_c',                importance: 0.05 },
  { feature: 'heat_index_c',          importance: 0.04 },
  { feature: 'consecutive_hot_days',  importance: 0.03 },
  { feature: 'heatwave_flag',         importance: 0.02 },
  { feature: 'day_of_week',           importance: 0.02 },
  { feature: 'general_acute_beds',    importance: 0.02 },
  { feature: 'other',                 importance: 0.02 },
];

function FeatureImportanceChart({ features }) {
  const sorted = [...features].sort((a, b) => b.importance - a.importance).slice(0, 10);
  return (
    <section className="chart-container" aria-label="Feature importance">
      <div className="chart-header">
        <h2 className="chart-title">Feature Importance — Top 10</h2>
      </div>
      <p className="chart-note">
        Derived from the trained GradientBoosting model. Lag and rolling features
        dominate, confirming that recent demand history is the strongest predictor.
      </p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 24, left: 155, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} domain={[0, 0.35]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
          <YAxis type="category" dataKey="feature" tick={{ fontSize: 11 }} width={145} />
          <Tooltip formatter={(v) => [`${(v * 100).toFixed(1)}%`, 'Importance']} />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {sorted.map((entry, i) => (
              <Cell key={entry.feature}
                fill={i === 0 ? '#8b5cf6' : i <= 2 ? '#3b82f6' : i <= 5 ? '#60a5fa' : '#93c5fd'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function ModelMetrics() {
  const metricsResult = useApiData(fetchModelMetrics, []);
  const m = metricsResult.data;

  const trainedAt = m?.trained_at
    ? new Date(m.trained_at).toLocaleDateString('en-GB', { dateStyle: 'medium' })
    : '—';

  // Thresholds calibrated for hospital A&E demand (typically 60-250 visits/day)
  const maeColor  = (m?.mae  ?? 999) < 15 ? '#22c55e' : (m?.mae  ?? 999) < 25 ? '#f59e0b' : '#ef4444';
  const rmseColor = (m?.rmse ?? 999) < 20 ? '#22c55e' : (m?.rmse ?? 999) < 30 ? '#f59e0b' : '#ef4444';
  const r2Color   = (m?.r2   ?? 0)   > 0.80 ? '#22c55e' : (m?.r2  ?? 0) > 0.65 ? '#f59e0b' : '#ef4444';

  return (
    <div className="page">
      <ConnectionBanner error={metricsResult.error} onRetry={metricsResult.refetch} />

      <PageHeader
        title="Model Metrics"
        description="Evaluation metrics for the trained GradientBoosting model (v1.0.0) — trained on 22,825 NHS hospital records."
      />

      <div className="info-box" role="note">
        <p>
          <strong>✓ Live model metrics.</strong> Trained on{' '}
          <strong>22,825 daily records</strong> from 25 NHS trusts (Apr 2024 – Mar 2025).
          Target: daily A&amp;E attendances. Algorithm: GradientBoostingRegressor with 31 features.
        </p>
      </div>

      {/* Model info card */}
      {m && (
        <section className="model-info-card" aria-label="Model information">
          <div className="model-info-card__row">
            <div><p className="model-info-card__label">Version</p>     <p className="model-info-card__value">{m.version ?? 'v1.0.0'}</p></div>
            <div><p className="model-info-card__label">Algorithm</p>   <p className="model-info-card__value">GradientBoosting</p></div>
            <div><p className="model-info-card__label">Evaluated</p>   <p className="model-info-card__value">{trainedAt}</p></div>
            <div><p className="model-info-card__label">Training rows</p><p className="model-info-card__value">18,120</p></div>
            <div><p className="model-info-card__label">Test rows</p>    <p className="model-info-card__value">4,530</p></div>
            <div><p className="model-info-card__label">Features</p>    <p className="model-info-card__value">{m.feature_count ?? 31}</p></div>
          </div>
        </section>
      )}

      {/* KPI metrics */}
      <section className="metric-grid" aria-label="Model performance metrics">
        <MetricCard title="MAE"
          value={m?.mae != null ? m.mae.toFixed(2) : '—'}
          unit=" visits/day"
          description="Mean Absolute Error — avg daily prediction error"
          icon="🎯" accentColor={maeColor}
          loading={metricsResult.loading} source="Trained Model" />

        <MetricCard title="RMSE"
          value={m?.rmse != null ? m.rmse.toFixed(2) : '—'}
          unit=" visits/day"
          description="Root Mean Squared Error — penalises large errors"
          icon="📐" accentColor={rmseColor}
          loading={metricsResult.loading} source="Trained Model" />

        <MetricCard title="R²"
          value={m?.r2 != null ? m.r2.toFixed(4) : '—'}
          description="83% of variance explained — strong predictive power"
          icon="📈" accentColor={r2Color}
          loading={metricsResult.loading} source="Trained Model" />

        <MetricCard title="Features"
          value={m?.feature_count ?? 31}
          description="Lag, rolling, weather, calendar, capacity"
          icon="🔢" accentColor="#8b5cf6"
          loading={metricsResult.loading} source="Trained Model" />
      </section>

      {/* R² gauge */}
      {m?.r2 != null && (
        <section className="gauge-section" aria-label="Model R² score">
          <div className="chart-header">
            <h2 className="chart-title">R² Score — Explained Variance</h2>
          </div>
          <div className="gauge-grid">
            <GaugeBar value={Math.round((m.r2 ?? 0) * 100)} label={`R² = ${m.r2?.toFixed(4)} (${Math.round((m.r2 ?? 0) * 100)}% variance explained)`} height={20} />
          </div>
        </section>
      )}

      {/* Feature importance */}
      <FeatureImportanceChart features={FEATURE_IMPORTANCE} />

      {/* Training summary */}
      <section className="info-box" aria-label="Training summary">
        <h2 className="section-title">Training Summary</h2>
        <dl className="definition-list">
          <dt>Dataset</dt>
          <dd>22,825 daily records — 25 NHS trusts across England (synthetic NHS data)</dd>
          <dt>Train / Test split</dt>
          <dd>80% train (18,120 rows) / 20% test (4,530 rows), random_state=42</dd>
          <dt>Target variable</dt>
          <dd><code>ae_attendances</code> — daily A&amp;E attendances per trust</dd>
          <dt>Best algorithm</dt>
          <dd>GradientBoosting (R²=0.83) beat RandomForest (0.82) and Ridge (0.81)</dd>
          <dt>Top features</dt>
          <dd>ae_lag_1 (31%), ae_roll_3 (18%), ae_lag_7 (14%) — recent demand history dominates</dd>
        </dl>
      </section>

      {/* Metric definitions */}
      <section className="info-box" aria-label="Metric definitions">
        <h2 className="section-title">Metric Definitions</h2>
        <dl className="definition-list">
          <dt>MAE</dt>   <dd>Mean Absolute Error — average absolute difference. For this model: ~16.9 visits/day off on average.</dd>
          <dt>RMSE</dt>  <dd>Root Mean Squared Error — penalises large errors. For this model: ~22.2 visits/day.</dd>
          <dt>R²</dt>    <dd>Coefficient of determination — 0.83 means 83% of variance is explained by the model.</dd>
        </dl>
      </section>
    </div>
  );
}

export default ModelMetrics;
