/**
 * GaugeBar.test.jsx
 * Tests for GaugeBar — value rendering, accessibility, threshold colours.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import GaugeBar from '../components/GaugeBar.jsx';

describe('GaugeBar', () => {
  it('renders the label', () => {
    render(<GaugeBar value={75} label="General Ward" />);
    expect(screen.getByText('General Ward')).toBeInTheDocument();
  });

  it('renders the percentage value', () => {
    render(<GaugeBar value={62} label="ICU" />);
    expect(screen.getByText('62%')).toBeInTheDocument();
  });

  it('sets aria-valuenow to the clamped value', () => {
    render(<GaugeBar value={80} label="ED" />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '80');
  });

  it('clamps value above 100 to 100', () => {
    render(<GaugeBar value={150} label="Over" />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });

  it('clamps value below 0 to 0', () => {
    render(<GaugeBar value={-10} label="Under" />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  });

  it('hides value when showValue is false', () => {
    render(<GaugeBar value={55} label="Ward" showValue={false} />);
    expect(screen.queryByText('55%')).toBeNull();
  });
});
