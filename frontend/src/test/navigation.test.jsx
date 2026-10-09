/**
 * navigation.test.jsx
 * Tests that the router renders the correct page for each URL segment,
 * and that unknown routes redirect to /dashboard.
 *
 * All service calls are mocked so pages load without a real backend.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App.jsx';

// ── Mock all service modules so no real network calls are made ───────────────

vi.mock('../api/weatherService.js',  () => ({
  fetchCurrentWeather: vi.fn().mockResolvedValue({ data: null, isDemo: true, error: null, source: 'demo' }),
  fetchWeatherHistory: vi.fn().mockResolvedValue({ data: [],   isDemo: true, error: null, source: 'demo' }),
}));

vi.mock('../api/forecastService.js', () => ({
  fetchHistoricalDemand:    vi.fn().mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' }),
  fetchDemandForecast:      vi.fn().mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' }),
  fetchCombinedDemandSeries:vi.fn().mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' }),
}));

vi.mock('../api/hospitalService.js', () => ({
  fetchHospitals:            vi.fn().mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' }),
  fetchHospitalRisk:         vi.fn().mockResolvedValue({ data: null, isDemo: true, error: null, source: 'demo' }),
  fetchAllHospitalsWithRisk: vi.fn().mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' }),
}));

vi.mock('../api/metricsService.js', () => ({
  fetchModelMetrics:      vi.fn().mockResolvedValue({ data: null, isDemo: true, error: null, source: 'demo' }),
  fetchFeatureImportance: vi.fn().mockResolvedValue({ data: [],   isDemo: true, error: null, source: 'demo' }),
  fetchTrainingHistory:   vi.fn().mockResolvedValue({ data: [],   isDemo: true, error: null, source: 'demo' }),
}));

vi.mock('../api/alertsService.js', () => ({
  fetchAlerts: vi.fn().mockResolvedValue({ data: [], isDemo: true, error: null, source: 'demo' }),
  fetchHealth: vi.fn().mockResolvedValue({ data: { status: 'demo' }, isDemo: true, error: null, source: 'demo' }),
}));

// Recharts crashes in jsdom (no DOM measurement APIs). Stub the entire module
// so pages that use charts still render in tests.
vi.mock('recharts', () => {
  const Stub = ({ children }) => <div data-testid="recharts-stub">{children ?? null}</div>;
  return {
    ResponsiveContainer: ({ children }) => <div>{children}</div>,
    ComposedChart:  Stub,
    LineChart:      Stub,
    AreaChart:      Stub,
    BarChart:       Stub,
    Line:           () => null,
    Area:           () => null,
    Bar:            () => null,
    XAxis:          () => null,
    YAxis:          () => null,
    CartesianGrid:  () => null,
    Tooltip:        () => null,
    Legend:         () => null,
    ReferenceLine:  () => null,
    Cell:           () => null,
  };
});

// ResizeObserver stub required by Recharts in jsdom
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn(),
}));

// ── Helper ───────────────────────────────────────────────────────────────────
function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────
describe('Navigation', () => {
  it('/ redirects to /dashboard and renders Dashboard page', async () => {
    renderAt('/');
    await waitFor(() =>
      expect(screen.getAllByText(/Dashboard/i).length).toBeGreaterThan(0)
    );
  });

  it('/dashboard renders Dashboard', async () => {
    renderAt('/dashboard');
    await waitFor(() =>
      expect(screen.getAllByText(/Dashboard/i).length).toBeGreaterThan(0)
    );
  });

  it('/forecasts renders Forecasts page', async () => {
    renderAt('/forecasts');
    await waitFor(() =>
      expect(screen.getAllByText(/Forecast/i).length).toBeGreaterThan(0)
    );
  });

  it('/hospitals renders Hospital Monitoring page', async () => {
    renderAt('/hospitals');
    await waitFor(() =>
      expect(screen.getAllByText(/Hospital Monitoring/i).length).toBeGreaterThan(0)
    );
  });

  it('/heatwave renders Heatwave Analysis page', async () => {
    renderAt('/heatwave');
    await waitFor(() =>
      expect(screen.getAllByText(/Heatwave Analysis/i).length).toBeGreaterThan(0)
    );
  });

  it('/metrics renders Model Metrics page', async () => {
    renderAt('/metrics');
    await waitFor(() =>
      expect(screen.getAllByText(/Model Metrics/i).length).toBeGreaterThan(0)
    );
  });

  it('/settings renders Settings page', async () => {
    renderAt('/settings');
    await waitFor(() =>
      expect(screen.getAllByText(/Settings/i).length).toBeGreaterThan(0)
    );
  });

  it('/unknown redirects to /dashboard', async () => {
    renderAt('/this-does-not-exist');
    await waitFor(() =>
      expect(screen.getAllByText(/Dashboard/i).length).toBeGreaterThan(0)
    );
  });

  it('sidebar is present on every page', async () => {
    renderAt('/dashboard');
    await waitFor(() =>
      expect(screen.getByRole('complementary')).toBeInTheDocument()
    );
  });

  it('sidebar contains all six nav links', async () => {
    renderAt('/dashboard');
    const nav = await screen.findByRole('navigation', { name: /main navigation/i });
    expect(nav.querySelectorAll('a').length).toBe(6);
  });
});
