import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts';

import MetricCard        from '../components/MetricCard.jsx';
import GaugeBar          from '../components/GaugeBar.jsx';
import PageHeader        from '../components/PageHeader.jsx';
import ConnectionBanner  from '../components/ConnectionBanner.jsx';

import { useApiData }                                          from '../api/useApiData.js';
import { fetchModelMetrics, fetchFeatureImportance, fetchTrainingHistory } from '../api/metricsService.js';

/**
 * ModelMetrics page
 *
 * Endpoints used:
 *   GET /metrics/model  — core MAE / RMSE / R² values
 *
 * Feature importance and training history have no backend endpoint yet
 * (not in api-contract.md). Those sections always show demo data and
 * are clearly labelled as such.
 */

function FeatureImportanceChart({ features, isDemo }) {
  const sorted = [...(features ?? [])].sort((a, b) => b.importance - a.importance);
  if (!sorted.length) return null;
  return (
    <section className="chart-container" aria-label="Feature importance">
      <div className="chart-header">
        <h2 className="chart-title">Feature Importance</h2>
        <span className="demo-badge">DEMO DATA — no endpoint yet</span>
      </div>
      <p className="chart-note">
        Placeholder values. The ML team has not yet added a feature importance endpoint.
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 24, left: 130, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} domain={[0, 0.25]} tickFormatter={(v) => v.toFixed(2)} />
          <YAxis type="category" dataKey="feature" tick={{ fontSize: 11 }} width={120} />
          <Tooltip formatter={(v) => [v.toFixed(3), 'Importance']} />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {sorted.map((entry, i) => (
              <Cell key={entry.feature} fill={i === 0 ? '#8b5cf6' : i <= 2 ? '#3b82f6' : '#93c5fd'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function TrainingHistoryTable({ runs }) {
  return (
    <section aria-label="Training run history">
      <div className="risk-table-header">
        <h2 className="chart-title" style={{ margin: 0 }}>Training Run History</h2>
        <span className="demo-badge">DEMO DATA — no endpoint yet</span>
      </div>
      <div className="risk-table-wrapper" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
        <table className="risk-table">
          <thead>
            <tr>
              <th scope="col">Run ID</th>
              <th scope="col">Date</th>
              <th scope="col">MAE</th>
              <th scope="col">RMSE</th>
              <th scope="col">R²</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {(runs ?? []).map((run) => (
              <tr key={run.run_id} className={run.status === 'current' ? 'risk-table__row--current' : ''}>
                <td><code>{run.run_id}</code></td>
                <td>{run.date}</td>
                <td>{run.mae}</td>
                <td>{run.rmse}</td>
                <td>{run.r2}</td>
                <td>
                  {run.status === 'current'
                    ? <span className="risk-badge" style={{ backgroundColor: '#22c55e' }}>CURRENT</span>
                    : <span className="text-muted">previous</span>
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

function ModelMetrics() {
  const metricsResult   = useApiData(fetchModelMetrics,       []);
  const featuresResult  = useApiData(fetchFeatureImportance,  []);
  const historyResult   = useApiData(fetchTrainingHistory,    []);

  const m = metricsResult.data;
  const metricsAreDemo = metricsResult.isDemo;

  const trainedAt = m?.trained_at
    ? new Date(m.trained_at).toLocaleString('en-AU', { dateStyle: 'medium', timeStyle: 'short' })
    : '—';

  // Baseline improvement — only compute if both values present
  const maeImprovement  = m?.baseline_mae  && m?.mae  ? Math.round(((m.baseline_mae  - m.mae)  / m.baseline_mae)  * 100) : null;
  const rmseImprovement = m?.baseline_rmse && m?.rmse ? Math.round(((m.baseline_rmse - m.rmse) / m.baseline_rmse) * 100) : null;

  const source = metricsAreDemo ? 'DEMO — synthetic data' : 'API';

  return (
    <div className="page">
      <ConnectionBanner isDemo={metricsAreDemo} error={metricsResult.error} onRetry={metricsResult.refetch} />

      <PageHeader
        title="Model Metrics"
        description={
          metricsAreDemo
            ? '⚠ Showing synthetic demo data. Connect the backend to see real model metrics.'
            : 'Live evaluation metrics from the most recent training run.'
        }
        badge={metricsAreDemo ? 'DEMO DATA' : null}
      />

      {/* Availability notice — shown whether demo or real, with different messages */}
      <div className={`info-box ${metricsAreDemo ? 'info-box--warning' : ''}`} role="note">
        <p>
          {metricsAreDemo
            ? <><strong>⚠ ML pipeline not connected.</strong> The metrics below are synthetic demo values for UI development only. Real metrics will appear here once the backend is integrated.</>
            : <><strong>✓ Live metrics.</strong> Values below are from the most recent model training run served by the connected backend.</>
          }
        </p>
      </div>

      {/* Model info */}
      {m && (
        <section className="model-info-card" aria-label="Model information">
          <div className="model-info-card__row">
            <div><p className="model-info-card__label">Model</p>      <p className="model-info-card__value">{m.model_name}</p></div>
            <div><p className="model-info-card__label">Version</p>    <p className="model-info-card__value">{m.version ?? '—'}</p></div>
            <div><p className="model-info-card__label">Trained at</p> <p className="model-info-card__value">{trainedAt}</p></div>
            <div><p className="model-info-card__label">Training rows</p><p className="model-info-card__value">{m.training_rows != null ? m.training_rows.toLocaleString() : '—'}</p></div>
            <div><p className="model-info-card__label">Features</p>   <p className="model-info-card__value">{m.feature_count ?? '—'}</p></div>
            <div><p className="model-info-card__label">Train time</p> <p className="model-info-card__value">{m.training_duration_s != null ? `${m.training_duration_s}s` : '—'}</p></div>
          </div>
          {metricsAreDemo && <span className="demo-badge" style={{ alignSelf: 'flex-start' }}>DEMO DATA</span>}
        </section>
      )}

      {/* Performance KPIs */}
      <section className="metric-grid" aria-label="Model performance metrics">
        <MetricCard title="MAE"         value={m?.mae  ?? '—'} unit=" admissions" description={maeImprovement  != null ? `${maeImprovement}% better than baseline`  : 'Baseline not available'} icon="🎯" accentColor={(m?.mae  ?? 999) < 10 ? '#22c55e' : '#f59e0b'} loading={metricsResult.loading} source={source} />
        <MetricCard title="RMSE"        value={m?.rmse ?? '—'} unit=" admissions" description={rmseImprovement != null ? `${rmseImprovement}% better than baseline` : 'Baseline not available'} icon="📐" accentColor={(m?.rmse ?? 999) < 12 ? '#22c55e' : '#f59e0b'} loading={metricsResult.loading} source={source} />
        <MetricCard title="R²"          value={m?.r2   ?? '—'} description="Closer to 1.0 is better" icon="📈" accentColor={(m?.r2 ?? 0) >= 0.85 ? '#22c55e' : (m?.r2 ?? 0) >= 0.7 ? '#f59e0b' : '#ef4444'} loading={metricsResult.loading} source={source} />
        <MetricCard title="MAPE"        value={m?.mape != null ? m.mape : '—'} unit={m?.mape != null ? '%' : ''} description={m?.mape == null ? 'Not in current API contract' : 'Mean Abs. % Error'} icon="📊" accentColor={(m?.mape ?? 999) < 10 ? '#22c55e' : '#f59e0b'} loading={metricsResult.loading} source={source} />
        <MetricCard title="Baseline MAE"  value={m?.baseline_mae  ?? '—'} unit={m?.baseline_mae  != null ? ' admissions' : ''} description={m?.baseline_mae  == null ? 'Not in current API contract' : 'Naïve mean model'} icon="📏" accentColor="#94a3b8" loading={metricsResult.loading} source={source} />
        <MetricCard title="Baseline RMSE" value={m?.baseline_rmse ?? '—'} unit={m?.baseline_rmse != null ? ' admissions' : ''} description={m?.baseline_rmse == null ? 'Not in current API contract' : 'Naïve mean model'} icon="📏" accentColor="#94a3b8" loading={metricsResult.loading} source={source} />
      </section>

      {/* Baseline gauges — only show if values present */}
      {(maeImprovement != null || rmseImprovement != null) && (
        <section className="gauge-section" aria-label="Improvement over baseline">
          <div className="chart-header">
            <h2 className="chart-title">Improvement over Naïve Baseline</h2>
            {metricsAreDemo && <span className="demo-badge">DEMO DATA</span>}
          </div>
          <div className="gauge-grid">
            {maeImprovement  != null && <GaugeBar value={maeImprovement}  label={`MAE reduction vs baseline (${maeImprovement}%)`}  height={18} />}
            {rmseImprovement != null && <GaugeBar value={rmseImprovement} label={`RMSE reduction vs baseline (${rmseImprovement}%)`} height={18} />}
            {m?.r2 != null && <GaugeBar value={Math.round(m.r2 * 100)} label={`R² score (${m.r2})`} height={18} />}
          </div>
        </section>
      )}

      {/* Feature importance — always demo */}
      <FeatureImportanceChart features={featuresResult.data} isDemo />

      {/* Training history — always demo */}
      <TrainingHistoryTable runs={historyResult.data} />

      {/* Definitions */}
      <section className="info-box" aria-label="Metric definitions">
        <h2 className="section-title">Metric Definitions</h2>
        <dl className="definition-list">
          <dt>MAE</dt>   <dd>Mean Absolute Error — average absolute difference. Lower is better.</dd>
          <dt>RMSE</dt>  <dd>Root Mean Squared Error — penalises large errors more. Lower is better.</dd>
          <dt>R²</dt>    <dd>Coefficient of determination — 1.0 is perfect, 0 means no predictive power.</dd>
          <dt>MAPE</dt>  <dd>Mean Absolute Percentage Error — error as % of actual. Not in current API contract.</dd>
          <dt>Baseline</dt><dd>Naïve model (always predicts the mean). Not in current API contract.</dd>
        </dl>
      </section>
    </div>
  );
}

export default ModelMetrics;
