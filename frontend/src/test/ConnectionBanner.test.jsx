/**
 * ConnectionBanner.test.jsx
 * Tests for ConnectionBanner component — all render conditions.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ConnectionBanner from '../components/ConnectionBanner.jsx';
import { ApiError } from '../api/client.js';

describe('ConnectionBanner', () => {
  it('renders nothing when isDemo is false', () => {
    const { container } = render(<ConnectionBanner isDemo={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the banner when isDemo is true', () => {
    render(<ConnectionBanner isDemo={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/Showing demo data/i)).toBeInTheDocument();
  });

  it('shows "Backend not configured" when no error provided', () => {
    render(<ConnectionBanner isDemo={true} />);
    expect(screen.getByText(/Backend not configured/i)).toBeInTheDocument();
  });

  it('shows network error message when error.isNetwork is true', () => {
    const err = new ApiError({ message: 'net fail', isNetwork: true, raw: new Error() });
    render(<ConnectionBanner isDemo={true} error={err} />);
    expect(screen.getByText(/Cannot reach backend/i)).toBeInTheDocument();
  });

  it('shows timeout message when error.isTimeout is true', () => {
    const err = new ApiError({ message: 'timeout', isTimeout: true, raw: new Error() });
    render(<ConnectionBanner isDemo={true} error={err} />);
    expect(screen.getByText(/timed out/i)).toBeInTheDocument();
  });

  it('shows HTTP status when error has a status code', () => {
    const err = new ApiError({ message: 'HTTP 503', status: 503, raw: new Error() });
    render(<ConnectionBanner isDemo={true} error={err} />);
    expect(screen.getByText(/HTTP 503/i)).toBeInTheDocument();
  });

  it('renders Retry button when onRetry is provided', () => {
    render(<ConnectionBanner isDemo={true} onRetry={vi.fn()} />);
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('does not render Retry button when onRetry is absent', () => {
    render(<ConnectionBanner isDemo={true} />);
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('calls onRetry when Retry is clicked', () => {
    const onRetry = vi.fn();
    render(<ConnectionBanner isDemo={true} onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
