/**
 * DemandChart.test.jsx
 * Tests for DemandChart — loading, empty, error, and data states.
 * Recharts uses SVG; we verify the container accessibility rather than SVG internals.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import DemandChart from '../components/DemandChart.jsx';

// Recharts uses ResizeObserver which is not in jsdom — stub it
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe:   vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Recharts ComposedChart/LineChart rely on DOM measurement APIs not present in
// jsdom and crash on render. Stub the entire recharts module so we can test
// the DemandChart wrapper logic (loading/empty/error states) without SVG errors.
vi.mock('recharts', () => {
  const Stub = ({ children }) => <div data-testid="recharts-stub">{children}</div>;
  return {
    ResponsiveContainer: ({ children }) => <div>{children}</div>,
    ComposedChart:  Stub,
    LineChart:      Stub,
    AreaChart:      Stub,
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
    BarChart:       Stub,
  };
});

const SAMPLE_DATA = [
  { date: '2024-09-28', admissions: 90, er_visits: 160, predicted_admissions: null, upper_ci: null, lower_ci: null, type: 'historical' },
  { date: '2024-10-02', admissions: null, er_visits: null, predicted_admissions: 105, upper_ci: 115, lower_ci: 95, type: 'forecast' },
];

describe('DemandChart', () => {
  it('shows loading skeleton when loading=true', () => {
    const { container } = render(<DemandChart data={[]} loading={true} title="Test Chart" />);
    expect(container.querySelector('.chart-skeleton')).toBeInTheDocument();
  });

  it('shows empty state when data is empty and not loading', () => {
    render(<DemandChart data={[]} loading={false} title="Test Chart" />);
    expect(screen.getByText(/No data available/i)).toBeInTheDocument();
  });

  it('shows error state when error=true', () => {
    render(<DemandChart data={[]} loading={false} error={true} title="Test Chart" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/could not be loaded/i)).toBeInTheDocument();
  });

  it('renders section with title when data is present', () => {
    render(
      <DemandChart
        data={SAMPLE_DATA}
        xKey="date"
        lines={[{ key: 'admissions', color: '#3b82f6', label: 'Admissions' }]}
        title="Demand History"
        loading={false}
      />
    );
    expect(screen.getByRole('region', { name: 'Demand History' })).toBeInTheDocument();
    expect(screen.getByText('Demand History')).toBeInTheDocument();
  });

  it('shows DEMO DATA badge', () => {
    render(
      <DemandChart data={SAMPLE_DATA} xKey="date" lines={[]} title="Chart" loading={false} />
    );
    expect(screen.getByText('DEMO DATA')).toBeInTheDocument();
  });
});
