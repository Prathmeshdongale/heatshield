import React from 'react';
import { NavLink } from 'react-router-dom';

/**
 * Sidebar — persistent left-hand navigation.
 * Uses React Router NavLink so the active route is highlighted automatically.
 */

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard',          icon: '🏠' },
  { path: '/forecasts', label: 'Forecasts',           icon: '📈' },
  { path: '/hospitals', label: 'Hospital Monitoring', icon: '🏥' },
  { path: '/heatwave',  label: 'Heatwave Analysis',   icon: '🌡️' },
  { path: '/metrics',   label: 'Model Metrics',       icon: '📊' },
  { path: '/settings',  label: 'Settings',            icon: '⚙️' },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-icon">🛡️</span>
        <span className="sidebar-brand-name">ThermoCare</span>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        <ul>
          {NAV_ITEMS.map(({ path, label, icon }) => (
            <li key={path}>
              <NavLink
                to={path}
                className={({ isActive }) =>
                  `sidebar-link${isActive ? ' sidebar-link--active' : ''}`
                }
              >
                <span className="sidebar-link-icon" aria-hidden="true">{icon}</span>
                <span className="sidebar-link-label">{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <span style={{ fontSize: 11, color: '#94a3b8' }}>HeatShield v1.0</span>
      </div>
    </aside>
  );
}

export default Sidebar;
