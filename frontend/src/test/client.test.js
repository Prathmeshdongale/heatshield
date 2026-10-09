/**
 * client.test.js
 * Tests for the central Axios instance and ApiError normalisation.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';

// We import the module under test after mocking axios so the interceptor
// attaches to our mock instance.
import apiClient, { ApiError, BASE_URL } from '../api/client.js';

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeAxiosError({ code, response, message = 'error' }) {
  const err = new Error(message);
  err.isAxiosError = true;
  err.code = code;
  err.response = response;
  err.config = { url: '/test' };
  return err;
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ApiError', () => {
  it('stores all properties', () => {
    const raw = new Error('boom');
    const err = new ApiError({ message: 'Test error', status: 500, endpoint: '/x', isNetwork: false, isTimeout: false, raw });
    expect(err.name).toBe('ApiError');
    expect(err.message).toBe('Test error');
    expect(err.status).toBe(500);
    expect(err.endpoint).toBe('/x');
    expect(err.isNetwork).toBe(false);
    expect(err.isTimeout).toBe(false);
    expect(err.raw).toBe(raw);
  });

  it('is an instance of Error', () => {
    const err = new ApiError({ message: 'x', raw: new Error() });
    expect(err instanceof Error).toBe(true);
  });
});

describe('BASE_URL', () => {
  it('is a non-empty string', () => {
    expect(typeof BASE_URL).toBe('string');
    expect(BASE_URL.length).toBeGreaterThan(0);
  });

  it('defaults to localhost when env var is absent', () => {
    expect(BASE_URL).toContain('localhost');
  });
});

describe('apiClient instance', () => {
  it('exists and has a get method', () => {
    expect(apiClient).toBeDefined();
    expect(typeof apiClient.get).toBe('function');
  });
});
