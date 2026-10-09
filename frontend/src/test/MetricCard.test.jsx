/**
 * MetricCard.test.jsx
 * Tests for the MetricCard component — all states.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricCard from '../components/MetricCard.jsx';

describe('MetricCard', () => {
  it('renders title and value', () => {
    render(<MetricCard title="Temperature" value={34} unit="°C" />);
    expect(screen.getByText('Temperature')).toBeInTheDocument();
    expect(screen.getByText('34')).toBeInTheDocument();
  });

  it('renders unit when provided', () => {
    render(<MetricCard title="Humidity" value={72} unit="%" />);
    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(<MetricCard title="Beds" value={400} description="200 available" />);
    expect(screen.getByText('200 available')).toBeInTheDocument();
  });

  it('renders icon when provided', () => {
    render(<MetricCard title="Test" value={1} icon="🔥" />);
    expect(screen.getByText('🔥')).toBeInTheDocument();
  });

  it('renders trend label', () => {
    render(<MetricCard title="Test" value={1} trend="up" trendLabel="Increasing" />);
    expect(screen.getByText(/Increasing/i)).toBeInTheDocument();
  });

  it('renders source text', () => {
    render(<MetricCard title="Test" value={1} source="DEMO" />);
    expect(screen.getByText(/DEMO/i)).toBeInTheDocument();
  });

  it('shows skeleton when loading=true', () => {
    const { container } = render(<MetricCard title="Test" value={1} loading={true} />);
    expect(container.querySelector('.metric-card--skeleton')).toBeInTheDocument();
    expect(screen.queryByText('1')).toBeNull();
  });

  it('shows error state when error=true', () => {
    render(<MetricCard title="Test" value={1} error={true} />);
    expect(screen.getByText(/Data unavailable/i)).toBeInTheDocument();
  });

  it('has accessible aria-label combining title and value', () => {
    render(<MetricCard title="Heat Index" value={42} unit="°C" />);
    expect(screen.getByRole('article')).toHaveAttribute('aria-label', 'Heat Index: 42°C');
  });
});
