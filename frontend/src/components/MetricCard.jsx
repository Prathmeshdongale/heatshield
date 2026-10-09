import React from 'react';

/**
 * MetricCard — displays a single KPI tile.
 *
 * Props:
 *   title        {string}         — label shown above the value
 *   value        {string|number}  — primary displayed value
 *   unit         {string}         — optional unit suffix (e.g. "°C", "%")
 *   description  {string}         — optional sub-label below the value
 *   icon         {string}         — optional emoji/icon displayed top-right
 *   trend        {string}         — "up" | "down" | "neutral"
 *   trendLabel   {string}         — human-readable trend description
 *   accentColor  {string}         — CSS colour for the left border accent
 *   loading      {boolean}        — show skeleton state
 *   error        {boolean}        — show error state
 *   source       {string}         — data source label (shown small)
 */
function MetricCard({
  title,
  value,
  unit = '',
  description,
  icon,
  trend,
  trendLabel,
  accentColor,
  loading = false,
  error = false,
  source,
}) {
  if (loading) {
    return (
      <article className="metric-card metric-card--skeleton" aria-busy="true" aria-label={`Loading ${title}`}>
        <div className="skeleton skeleton--text-sm" />
        <div className="skeleton skeleton--text-lg" />
        <div className="skeleton skeleton--text-sm" style={{ width: '60%' }} />
      </article>
    );
  }

  if (error) {
    return (
      <article className="metric-card metric-card--error" aria-label={`${title}: error loading data`}>
        <p className="metric-card__title">{title}</p>
        <p className="metric-card__error-msg">⚠ Data unavailable</p>
      </article>
    );
  }

  const trendIcon  = { up: '▲', down: '▼', neutral: '—' }[trend] ?? '';
  const trendClass = trend ? `metric-card__trend--${trend}` : '';
  const style      = accentColor ? { borderLeftColor: accentColor, borderLeftWidth: 3 } : {};

  return (
    <article
      className="metric-card"
      style={style}
      aria-label={`${title}: ${value}${unit}`}
    >
      <div className="metric-card__header">
        <p className="metric-card__title">{title}</p>
        {icon && <span className="metric-card__icon" aria-hidden="true">{icon}</span>}
      </div>

      <p className="metric-card__value">
        {value}
        {unit && <span className="metric-card__unit"> {unit}</span>}
      </p>

      {description && (
        <p className="metric-card__description">{description}</p>
      )}

      {trend && (
        <p className={`metric-card__trend ${trendClass}`} aria-label={`Trend: ${trendLabel ?? trend}`}>
          {trendIcon} {trendLabel ?? trend}
        </p>
      )}

      {source && (
        <p className="metric-card__source">{source}</p>
      )}
    </article>
  );
}

export default MetricCard;
