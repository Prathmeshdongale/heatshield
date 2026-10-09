import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Forecasts from './pages/Forecasts.jsx';
import HospitalMonitoring from './pages/HospitalMonitoring.jsx';
import HeatwaveAnalysis from './pages/HeatwaveAnalysis.jsx';
import ModelMetrics from './pages/ModelMetrics.jsx';
import Settings from './pages/Settings.jsx';

/**
 * App — root router.
 * All pages are rendered inside the shared Layout (sidebar + header).
 * The default route redirects to /dashboard.
 */
function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="forecasts" element={<Forecasts />} />
        <Route path="hospitals" element={<HospitalMonitoring />} />
        <Route path="heatwave" element={<HeatwaveAnalysis />} />
        <Route path="metrics" element={<ModelMetrics />} />
        <Route path="settings" element={<Settings />} />
        {/* Catch-all: redirect unknown routes back to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
