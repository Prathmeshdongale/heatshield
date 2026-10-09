import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    open: true,
  },

  // ── Vitest configuration ──────────────────────────────────────────────────
  test: {
    // Simulate a browser-like DOM environment
    environment: 'jsdom',

    // Import @testing-library/jest-dom matchers globally in every test file
    setupFiles: ['./src/test/setup.js'],

    // Coverage provider
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/test/**', 'src/data/**', 'src/styles/**'],
      reporter: ['text', 'html'],
    },

    // Allow JSX in test files without an explicit import
    globals: true,
  },
});
