/**
 * RiskTable.test.jsx
 * Tests for RiskTable — all states: loading, empty, error, populated.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RiskTable from '../components/RiskTable.jsx';

const SAMPLE_ROWS = [
  { hospital_id: 'H001', name: 'City General', region: 'North', occupancy_pct: 88, icu_occupancy_pct: 92, risk_level: 'critical', predicted_surge: 18 },
  { hospital_id: 'H002', name: 'Eastside MC',  region: 'East',  occupancy_pct: 76, icu_occupancy_pct: 71, risk_level: 'high',     predicted_surge: 12 },
];

describe('RiskTable', () => {
  it('shows loading text when loading=true', () => {
    render(<RiskTable rows={[]} loading={true} />);
    // Skeleton rows should be rendered (aria-hidden), no data text
    expect(screen.queryByText(/No hospital data/i)).toBeNull();
  });

  it('shows empty state when rows array is empty', () => {
    render(<RiskTable rows={[]} loading={false} />);
    expect(screen.getByText(/No hospital data available/i)).toBeInTheDocument();
  });

  it('shows error message when error=true', () => {
    render(<RiskTable rows={[]} loading={false} error={true} />);
    expect(screen.getByText(/Could not load hospital data/i)).toBeInTheDocument();
  });

  it('renders one row per hospital', () => {
    render(<RiskTable rows={SAMPLE_ROWS} loading={false} />);
    expect(screen.getByText('City General')).toBeInTheDocument();
    expect(screen.getByText('Eastside MC')).toBeInTheDocument();
  });

  it('renders region for each hospital', () => {
    render(<RiskTable rows={SAMPLE_ROWS} loading={false} />);
    expect(screen.getByText('North')).toBeInTheDocument();
    expect(screen.getByText('East')).toBeInTheDocument();
  });

  it('renders risk badges', () => {
    render(<RiskTable rows={SAMPLE_ROWS} loading={false} />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  it('renders the section as a landmark region', () => {
    render(<RiskTable rows={SAMPLE_ROWS} loading={false} />);
    expect(screen.getByRole('region', { name: /hospital capacity risk table/i })).toBeInTheDocument();
  });
});
