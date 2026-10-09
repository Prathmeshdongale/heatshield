import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts';

import MetricCard        from '../components/MetricCard.jsx';
import GaugeBar          from '../components/GaugeBar.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }            from '../api/useApiData.js';
import { fetchModelMetrics }     from '../api/metricsService.js';

function ModelMetrics() {
  const metricsResult = useApiData(fetchModelMetrics, []);
  const m = metricsResult.data;

  const trainedAt = m?.trained_at
    ? new Date(m.trained_at).toLocaleString('en-AU', { dateStyle: 'medium' })
    : '—';

  const maeImprovement  = m?.baseline_mae  && m?.mae
    ? Math.round(((m.baseline_mae  - m.mae)  / m.baseline_mae)  * 100) : null;
  const rmseImprovement = m?.baseline_rmse && m?.rmse
    ? Math.round(((m.baseline_rmse - m.rmse) / m.baseline_rmse) * 100) : null;

  return (
    <div className="page">
      <ConnectionBanner error={metricsResult.error} onRetry={metricsResult.refetch} />

      <PageHeader
        title="Model Metrics"
        description="Evaluation metrics from the most recent training run, served from Supabase."
      />

      <div className="info-box" role="note">
        <p><strong>✓ Live metrics.</strong> Values below are from the most recent model
        training run stored in Supabase.</p>
      </div>

      {m && (
        <section className="model-info-card" aria-label="Model information">
          <div className="model-info-card__row">
            <div><p className="model-info-card__label">Model</p>      <p className="model-info-card__value">{m.model_name}</p></div>
            <div><p className="model-info-card__label">Version</p>    <p className="model-info-card__value">{m.version ?? '—'}</p></div>
            <div><p className="model-info-card__label">Evaluated on</p><p className="model-info-card__value">{trainedAt}</p></div>
            <div><p className="model-info-card__label">Features</p>   <p className="model-info-card__value">{m.feature_count ?? '—'}</p></div>
          </div>
        </section>
      )}

      <section className="metric-grid" aria-label="Model performance metrics">
        <MetricCard title="MAE"  value={m?.mae  ?? '—'} unit=" admissions"
          description="Mean Absolute Error — lower is better"
          icon="🎯" accentColor={(m?.mae  ?? 999) < 10 ? '#22c55e' : '#f59e0b'}
          loading={metricsResult.loading} source="Supabase" />
        <MetricCard title="RMSE" value={m?.rmse ?? '—'} unit=" admissions"
          description="Root Mean Squared Error — lower is better"
          icon="📐" accentColor={(m?.rmse ?? 999) < 12 ? '#22c55e' : '#f59e0b'}
          loading={metricsResult.loading} source="Supabase" />
        <MetricCard title="R²"   value={m?.r2   ?? '—'}
          description="Coefficient of determination — closer to 1.0 is better"
          icon="📈" accentColor={(m?.r2 ?? 0) >= 0.85 ? '#22c55e' : (m?.r2 ?? 0) >= 0.7 ? '#f59e0b' : '#ef4444'}
          loading={metricsResult.loading} source="Supabase" />
        <MetricCard title="Feature Count" value={m?.feature_count ?? '—'}
          description="Number of model input features"
          icon="🔢" accentColor="#8b5cf6"
          loading={metricsResult.loading} source="Supabase" />
      </section>

      {m?.r2 != null && (
        <section className="gauge-section" aria-label="Model R² score">
          <div className="chart-header">
            <h2 className="chart-title">Model R² Score</h2>
          </div>
          <div className="gauge-grid">
            <GaugeBar value={Math.round(m.r2 * 100)} label={`R² = ${m.r2}`} height={18} />
            {maeImprovement  != null && <GaugeBar value={maeImprovement}  label={`MAE improvement vs baseline (${maeImprovement}%)`} height={18} />}
            {rmseImprovement != null && <GaugeBar value={rmseImprovement} label={`RMSE improvement vs baseline (${rmseImprovement}%)`} height={18} />}
          </div>
        </section>
      )}

      <section className="info-box" aria-label="Metric definitions">
        <h2 className="section-title">Metric Definitions</h2>
        <dl className="definition-list">
          <dt>MAE</dt>   <dd>Mean Absolute Error — average absolute difference between predicted and actual. Lower is better.</dd>
          <dt>RMSE</dt>  <dd>Root Mean Squared Error — penalises large errors more heavily. Lower is better.</dd>
          <dt>R²</dt>    <dd>Coefficient of determination — 1.0 is perfect, 0 means no predictive power.</dd>
        </dl>
      </section>
    </div>
  );
}

export default ModelMetrics;
