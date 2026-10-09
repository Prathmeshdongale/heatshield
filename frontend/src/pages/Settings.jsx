import React, { useState } from 'react';
import PageHeader        from '../components/PageHeader.jsx';
import { BASE_URL }      from '../api/client.js';
import { useHealthCheck } from '../api/useHealthCheck.js';
import { SETTINGS_DEFAULTS } from '../data/demoPages.js';

/**
 * Settings page
 *
 * Sections:
 *   1. API configuration (backend URL)
 *   2. Display preferences (temperature unit, date format, refresh interval)
 *   3. Connection status (live from health endpoint)
 *   4. About
 */

const LS_KEY = 'hs_settings';

function loadSettings() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? { ...SETTINGS_DEFAULTS, ...JSON.parse(raw) } : { ...SETTINGS_DEFAULTS };
  } catch {
    return { ...SETTINGS_DEFAULTS };
  }
}

function saveSettings(s) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(s)); } catch {}
}

function SettingsSection({ title, children }) {
  const id = `settings-${title.replace(/\s/g, '-').toLowerCase()}`;
  return (
    <section className="settings-section" aria-labelledby={id}>
      <h2 className="section-title" id={id}>{title}</h2>
      {children}
    </section>
  );
}

function StatusDot({ ok, label }) {
  const color = ok ? '#22c55e' : '#ef4444';
  return (
    <span className="status-dot" aria-label={label}>
      <span className="status-dot__circle" style={{ backgroundColor: color }} aria-hidden="true" />
      <span className="status-dot__label" style={{ color }}>{label}</span>
    </span>
  );
}

function Settings() {
  const [settings, setSettings] = useState(loadSettings);
  const [saved,    setSaved]    = useState(false);
  const [errors,   setErrors]   = useState({});
  const { isLive, dbConnected, modelLoaded, modelVersion, loading: healthLoading } = useHealthCheck();

  function update(key, value) {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => { const e = { ...prev }; delete e[key]; return e; });
  }

  function validate(s) {
    const errs = {};
    if (s.apiBaseUrl && !/^https?:\/\/.+/.test(s.apiBaseUrl)) {
      errs.apiBaseUrl = 'Must be a valid http:// or https:// URL, or leave blank.';
    }
    if (![60_000, 120_000, 300_000, 600_000].includes(Number(s.refreshIntervalMs))) {
      errs.refreshIntervalMs = 'Select a valid refresh interval.';
    }
    return errs;
  }

  function handleSave(e) {
    e.preventDefault();
    const errs = validate(settings);
    if (Object.keys(errs).length) { setErrors(errs); return; }
    saveSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  function handleReset() {
    setSettings({ ...SETTINGS_DEFAULTS });
    saveSettings(SETTINGS_DEFAULTS);
    setErrors({});
    setSaved(false);
  }

  return (
    <div className="page settings-page">

      <PageHeader
        title="Settings"
        description="Configure display preferences and API connection. Settings are stored locally in your browser."
      />

      <form onSubmit={handleSave} noValidate>

        {/* ── API Configuration ─────────────────────────────────── */}
        <SettingsSection title="API Configuration">
          <p className="page-description" style={{ marginBottom: 16 }}>
            Override the backend API URL. Leave blank to use{' '}
            <code>VITE_API_BASE_URL</code> from <code>.env</code>.
            Currently: <code>{BASE_URL}</code>
          </p>
          <div className="form-group">
            <label htmlFor="api-url" className="form-label">Backend API Base URL</label>
            <input
              id="api-url" type="url"
              className={`form-input${errors.apiBaseUrl ? ' form-input--error' : ''}`}
              value={settings.apiBaseUrl}
              onChange={(e) => update('apiBaseUrl', e.target.value)}
              placeholder="http://localhost:8000/api/v1"
              aria-describedby="api-url-hint"
            />
            <p id="api-url-hint" className="form-hint">Stored in localStorage only.</p>
            {errors.apiBaseUrl && (
              <p className="form-error" role="alert">{errors.apiBaseUrl}</p>
            )}
          </div>
        </SettingsSection>

        {/* ── Display Preferences ───────────────────────────────── */}
        <SettingsSection title="Display Preferences">
          <div className="settings-prefs-grid">

            <div className="form-group">
              <label htmlFor="temp-unit" className="form-label">Temperature Unit</label>
              <select id="temp-unit" className="control-select"
                value={settings.temperatureUnit}
                onChange={(e) => update('temperatureUnit', e.target.value)}>
                <option value="celsius">Celsius (°C)</option>
                <option value="fahrenheit">Fahrenheit (°F)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="date-format" className="form-label">Date Format</label>
              <select id="date-format" className="control-select"
                value={settings.dateFormat}
                onChange={(e) => update('dateFormat', e.target.value)}>
                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="refresh-interval" className="form-label">Auto-Refresh Interval</label>
              <select id="refresh-interval"
                className={`control-select${errors.refreshIntervalMs ? ' form-input--error' : ''}`}
                value={settings.refreshIntervalMs}
                onChange={(e) => update('refreshIntervalMs', Number(e.target.value))}>
                <option value={60_000}>1 minute</option>
                <option value={120_000}>2 minutes</option>
                <option value={300_000}>5 minutes (default)</option>
                <option value={600_000}>10 minutes</option>
              </select>
              {errors.refreshIntervalMs && (
                <p className="form-error" role="alert">{errors.refreshIntervalMs}</p>
              )}
            </div>

          </div>
        </SettingsSection>

        <div className="settings-actions">
          <button type="submit" className="btn btn-primary">Save Settings</button>
          <button type="button" className="btn btn-ghost" onClick={handleReset}>Reset to Defaults</button>
          {saved && (
            <p className="form-success" role="status" aria-live="polite">✓ Settings saved.</p>
          )}
        </div>

      </form>

      {/* ── Connection Status ─────────────────────────────────────── */}
      <SettingsSection title="Connection Status">
        <div className="risk-table-wrapper">
          <table className="risk-table">
            <thead>
              <tr>
                <th scope="col">Service</th>
                <th scope="col">Status</th>
                <th scope="col">Detail</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 500 }}>Backend API</td>
                <td>
                  {healthLoading
                    ? <span className="text-muted">Checking…</span>
                    : <StatusDot ok={isLive} label={isLive ? 'Connected' : 'Unavailable'} />
                  }
                </td>
                <td className="text-muted">{BASE_URL}</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 500 }}>Supabase DB</td>
                <td>
                  {healthLoading
                    ? <span className="text-muted">Checking…</span>
                    : <StatusDot ok={dbConnected} label={dbConnected ? 'Connected' : 'Unavailable'} />
                  }
                </td>
                <td className="text-muted">
                  {dbConnected ? 'Tables exist, RLS active' : 'Run FULL_SETUP.sql to initialise'}
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 500 }}>ML Model</td>
                <td>
                  {healthLoading
                    ? <span className="text-muted">Checking…</span>
                    : <StatusDot ok={modelLoaded} label={modelLoaded ? 'Loaded' : 'Not loaded'} />
                  }
                </td>
                <td className="text-muted">
                  {modelLoaded
                    ? `GradientBoosting ${modelVersion ?? 'v1.0.0'} — 31 features, R²=0.83`
                    : 'Serving seeded DB forecasts (no model artifact)'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </SettingsSection>

      {/* ── About ────────────────────────────────────────────────── */}
      <SettingsSection title="About HeatShield">
        <dl className="about-list">
          <dt>Version</dt>         <dd>1.0.0</dd>
          <dt>Data source</dt>     <dd>Supabase (hospitals); Open-Meteo (temperature & humidity)</dd>
          <dt>Frontend stack</dt>  <dd>React 18, Vite 6, React Router 6, Recharts, Axios</dd>
          <dt>Backend stack</dt>   <dd>FastAPI, Python 3.12, httpx, Pydantic v2</dd>
          <dt>API contract</dt>    <dd>See <code>docs/api-contract.md</code> in the repository.</dd>
        </dl>
      </SettingsSection>

    </div>
  );
}

export default Settings;
