# HeatShield — Frontend Setup & Developer Guide

**Owner:** Member 1 — Frontend  
**Stack:** React 18, Vite 6, React Router 6, Recharts, Axios  
**Test framework:** Vitest 5 + @testing-library/react

---

## Prerequisites

- Node.js 18 or later  
- npm 9 or later  
- Git

---

## Quick start

```bash
# 1. Clone the repo
git clone https://github.com/Prathmeshdongale/heatshield.git
cd heatshield/frontend

# 2. Install dependencies
npm install

# 3. Configure environment (see Environment Variables below)
Copy-Item .env.example .env

# 4. Start the development server
npm run dev
```

Opens automatically at **http://localhost:5173**.

---

## Environment Variables

Create a `.env` file at `frontend/.env` (already gitignored — never commit it).

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | No | Full base URL of the FastAPI backend, e.g. `http://localhost:8000/api/v1`. When absent, the frontend runs in **demo mode** with clearly labelled synthetic data. |

### Example `.env`

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Security rules

- **Never** put `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`, database passwords, or any other secret in this file.
- Only `VITE_API_BASE_URL` belongs here. The backend handles all Supabase communication.
- All `VITE_*` variables are embedded in the browser bundle — treat them as public.

---

## Available Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run test` | Run all tests once (CI mode) |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests and generate coverage report |
| `npm run lint` | ESLint check |

---

## Running Frontend + Backend Together

Open **two terminals**:

```bash
# Terminal 1 — Backend (Member 2's responsibility)
cd heatshield/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd heatshield/frontend
npm run dev
```

The frontend reads `VITE_API_BASE_URL` from `.env`. If the backend is not running the frontend automatically falls back to demo data with an amber banner.

---

## Demo Mode

When `VITE_API_BASE_URL` is not set, or the backend returns a network/HTTP error, every page falls back to **synthetic demo data**. This is intentional and explicit:

- An amber **"🔌 Showing demo data"** banner appears at the top of each page.
- All KPI cards show `Source: DEMO — synthetic data`.
- Every chart has a **DEMO DATA** badge.
- Demo data is located in `src/data/demoDashboard.js` and `src/data/demoPages.js`.

These values are computer-generated and **do not represent real hospital data, real forecasts, or any clinical information**.

---

## Project Structure

```
src/
├── api/
│   ├── client.js          # Axios instance + ApiError class
│   ├── serviceHelpers.js  # callApi() + withDemoFallback()
│   ├── useApiData.js      # React hook for service calls
│   ├── weatherService.js  # GET /weather/current, /weather/history
│   ├── forecastService.js # GET /demand/historical, /demand/forecast
│   ├── hospitalService.js # GET /hospitals, /hospitals/{id}/risk
│   ├── metricsService.js  # GET /metrics/model
│   └── alertsService.js   # GET /alerts (placeholder), /health
├── components/
│   ├── layout/            # Layout, Sidebar, Header
│   ├── MetricCard.jsx
│   ├── DemandChart.jsx
│   ├── WeatherChart.jsx
│   ├── RiskTable.jsx
│   ├── AlertsPanel.jsx
│   ├── StatusBanner.jsx
│   ├── ConnectionBanner.jsx
│   ├── PageHeader.jsx
│   └── GaugeBar.jsx
├── data/
│   ├── demoDashboard.js   # Dashboard demo data
│   └── demoPages.js       # Per-page demo data
├── pages/
│   ├── Dashboard.jsx
│   ├── Forecasts.jsx
│   ├── HospitalMonitoring.jsx
│   ├── HeatwaveAnalysis.jsx
│   ├── ModelMetrics.jsx
│   └── Settings.jsx
├── styles/
│   └── index.css
└── test/
    ├── setup.js
    ├── client.test.js
    ├── serviceHelpers.test.js
    ├── weatherService.test.js
    ├── forecastService.test.js
    ├── hospitalService.test.js
    ├── metricsService.test.js
    ├── useApiData.test.js
    ├── ConnectionBanner.test.jsx
    ├── MetricCard.test.jsx
    ├── GaugeBar.test.jsx
    ├── RiskTable.test.jsx
    ├── DemandChart.test.jsx
    └── navigation.test.jsx
```

---

## API Contract

The frontend consumes exactly the endpoints defined in `../docs/api-contract.md`:

| Endpoint | Service | Used by |
|---|---|---|
| `GET /health` | alertsService | Settings |
| `GET /weather/current` | weatherService | Dashboard, HeatwaveAnalysis |
| `GET /weather/history?days=N` | weatherService | Dashboard, HeatwaveAnalysis |
| `GET /demand/historical?days=N` | forecastService | Dashboard, Forecasts, HeatwaveAnalysis |
| `GET /demand/forecast?days=N` | forecastService | Dashboard, Forecasts |
| `GET /hospitals` | hospitalService | Dashboard, HospitalMonitoring, Forecasts |
| `GET /hospitals/{id}/risk` | hospitalService | HospitalMonitoring |
| `GET /metrics/model` | metricsService | ModelMetrics |

**Do not change endpoint names or response schemas without updating `docs/api-contract.md` first.**

---

## Test Results (as of last run)

```
Test Files  13 passed (13)
     Tests  91 passed (91)
  Duration  ~3s
```

Coverage: `src/api/` services, `useApiData` hook, and key UI components.

---

## Gitignore — What Is Protected

The root `.gitignore` blocks:

- `node_modules/`
- `.env`, `.env.*` (but **not** `.env.example`)
- `dist/`, `build/`, `out/`
- `coverage/`
- `*.log`
- `.vscode/`, `.idea/`

**Never commit `.env`.**
