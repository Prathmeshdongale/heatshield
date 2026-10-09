import React, { useState } from 'react';
import PageHeader from '../components/PageHeader.jsx';
import { SETTINGS_DEFAULTS, API_STATUS_DEMO } from '../data/demoPages.js';

/**
 * Settings page
 *
 * Sections:
 *   1. API configuration (base URL override)
 *   2. Display preferences (temperature unit, date format, refresh interval, demo badges)
 *   3. Connection status (shows whether backend/DB/ML are reachable)
 *   4. About / stack info
 *
 * Preferences are persisted in localStorage. Changes take effect on next
 * page load (except demo badge toggle, which is immediate via state).
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

function saveSettings(settings) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(settings));
  } catch {
    // Storage may be blocked in some environments — ignore silently
  }
}

// ── Sub-components ──────────────────────────────────────────────────────────

function SettingsSection({ title, children }) {
  return (
    <section className="settings-section" aria-labelledby={`settings-${title.replace(/\s/g, '-').toLowerCase()}`}>
      <h2
        className="section-title"
        id={`settings-${title.replace(/\s/g, '-').toLowerCase()}`}
      >
        {title}
      </h2>
      {children}
    </section>
  );
}

function StatusDot({ status }) {
  const meta = {
    available:   { color: '#22c55e', label: 'Available'   },
    unavailable: { color: '#ef4444', label: 'Unavailable' },
    degraded:    { color: '#f59e0b', label: 'Degraded'    },
  }[status] ?? { color: '#94a3b8', label: 'Unknown' };

  return (
    <span className="status-dot" aria-label={meta.label}>
      <span
        className="status-dot__circle"
        style={{ backgroundColor: meta.color }}
        aria-hidden="true"
      />
      <span className="status-dot__label" style={{ color: meta.color }}>
        {meta.label}
      </span>
    </span>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

function Settings() {
  const [settings, setSettings] = useState(loadSettings);
  const [saved,    setSaved]    = useState(false);
  const [errors,   setErrors]   = useState({});

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
        description="Configure display preferences and API connection. All settings are stored locally in your browser."
        badge={null}
      />

      <form onSubmit={handleSave} noValidate>

        {/* ── API configuration ────────────────────────────────── */}
        <SettingsSection title="API Configuration">
          <p className="page-description" style={{ marginBottom: 16 }}>
            Override the backend API URL. Leave blank to use the value from{' '}
            <code>.env</code> (<code>VITE_API_BASE_URL</code>).
            Changes take effect after page reload.
          </p>

          <div className="form-group">
            <label htmlFor="api-url" className="form-label">
              Backend API Base URL
            </label>
            <input
              id="api-url"
              type="url"
              className={`form-input${errors.apiBaseUrl ? ' form-input--error' : ''}`}
              value={settings.apiBaseUrl}
              onChange={(e) => update('apiBaseUrl', e.target.value)}
              placeholder="http://localhost:8000/api/v1"
              aria-describedby="api-url-hint api-url-error"
            />
            <p id="api-url-hint" className="form-hint">
              Stored in localStorage only. Never sent to any analytics service.
            </p>
            {errors.apiBaseUrl && (
              <p id="api-url-error" className="form-error" role="alert">
                {errors.apiBaseUrl}
              </p>
            )}
          </div>
        </SettingsSection>

        {/* ── Display preferences ──────────────────────────────── */}
        <SettingsSection title="Display Preferences">

          <div className="settings-prefs-grid">

            <div className="form-group">
              <label htmlFor="temp-unit" className="form-label">Temperature Unit</label>
              <select
                id="temp-unit"
                className="control-select"
                value={settings.temperatureUnit}
                onChange={(e) => update('temperatureUnit', e.target.value)}
              >
                <option value="celsius">Celsius (°C)</option>
                <option value="fahrenheit">Fahrenheit (°F)</option>
              </select>
              <p className="form-hint">Display unit for all temperature values.</p>
            </div>

            <div className="form-group">
              <label htmlFor="date-format" className="form-label">Date Format</label>
              <select
                id="date-format"
                className="control-select"
                value={settings.dateFormat}
                onChange={(e) => update('dateFormat', e.target.value)}
              >
                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              </select>
              <p className="form-hint">Format used in tables and charts.</p>
            </div>

            <div className="form-group">
              <label htmlFor="refresh-interval" className="form-label">
                Auto-Refresh Interval
              </label>
              <select
                id="refresh-interval"
                className={`control-select${errors.refreshIntervalMs ? ' form-input--error' : ''}`}
                value={settings.refreshIntervalMs}
                onChange={(e) => update('refreshIntervalMs', Number(e.target.value))}
              >
                <option value={60_000}>1 minute</option>
                <option value={120_000}>2 minutes</option>
                <option value={300_000}>5 minutes (default)</option>
                <option value={600_000}>10 minutes</option>
              </select>
              <p className="form-hint">
                How often the frontend polls the API (when backend is connected).
              </p>
              {errors.refreshIntervalMs && (
                <p className="form-error" role="alert">{errors.refreshIntervalMs}</p>
              )}
            </div>

            <div className="form-group">
              <fieldset style={{ border: 'none', padding: 0 }}>
                <legend className="form-label">Demo Data Badges</legend>
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    className="toggle-input"
                    checked={settings.showDemoBadges}
                    onChange={(e) => update('showDemoBadges', e.target.checked)}
                    aria-describedby="demo-badge-hint"
                  />
                  <span className="toggle-track" aria-hidden="true" />
                  <span>Show "DEMO DATA" badges on all panels</span>
                </label>
                <p id="demo-badge-hint" className="form-hint">
                  Recommended to keep enabled during development.
                </p>
              </fieldset>
            </div>

          </div>
        </SettingsSection>

        <div className="settings-actions">
          <button type="submit" className="btn btn-primary">Save Settings</button>
          <button type="button" className="btn btn-ghost" onClick={handleReset}>
            Reset to Defaults
          </button>
          {saved && (
            <p className="form-success" role="status" aria-live="polite">
              ✓ Settings saved.
            </p>
          )}
        </div>

      </form>

      {/* ── Connection status ────────────────────────────────────── */}
      <SettingsSection title="Connection Status">
        <p className="page-description" style={{ marginBottom: 12 }}>
          Status of backend services. All services show "unavailable" until the
          backend team's API is connected.
        </p>
        <div className="risk-table-wrapper">
          <table className="risk-table">
            <thead>
              <tr>
                <th scope="col">Service</th>
                <th scope="col">Status</th>
                <th scope="col">Note</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(API_STATUS_DEMO).map(([key, val]) => (
                <tr key={key}>
                  <td style={{ textTransform: 'capitalize', fontWeight: 500 }}>{key}</td>
                  <td><StatusDot status={val.status} /></td>
                  <td className="text-muted">{val.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SettingsSection>

      {/* ── About ────────────────────────────────────────────────── */}
      <SettingsSection title="About HeatShield">
        <dl className="about-list">
          <dt>Version</dt>       <dd>0.2.0 (pages complete — backend pending)</dd>
          <dt>Data</dt>          <dd>All data displayed is synthetic demo data. Not real clinical data.</dd>
          <dt>Frontend stack</dt><dd>React 18, Vite, React Router 6, Recharts, Axios</dd>
          <dt>API contract</dt>  <dd>See <code>docs/api-contract.md</code> in the repository.</dd>
          <dt>Owner</dt>         <dd>Member 1 — Frontend</dd>
        </dl>
      </SettingsSection>

    </div>
  );
}

export default Settings;
