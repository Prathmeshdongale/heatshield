# ThermoCare AI

ThermoCare AI helps hospitals anticipate heat-related demand surges. It combines weather signals, capacity data, and ML forecasts so operations teams can see risk early and act before beds run out.

> **Demo mode:** Out of the box the app runs on clearly labelled synthetic data. No Supabase credentials or ML artifact are required to explore the UI and API.

---

## Features

- **Hospital monitoring** ? live capacity, occupancy, and risk status (`green` / `amber` / `red` / `critical`)
- **Demand forecasting** ? multi-day admission predictions with confidence bands
- **Heatwave analysis** ? weather observations linked to hospital regions
- **Alerts** ? capacity-risk alerts when forecasted demand threatens beds
- **Model metrics** ? MAE, RMSE, R? and training window for the forecast model
- **Graceful fallback** ? if the database or ML model is unavailable, the stack serves demo data and surfaces a demo banner

---

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | React 18, Vite 6, React Router 6, Recharts, Axios |
| Backend | FastAPI, Pydantic, Uvicorn |
| Database | PostgreSQL (Supabase) with RLS |
| ML | joblib model artifact (optional; demo mode without it) |

---

## Project structure

```text
heatshield/
??? frontend/          # React + Vite dashboard
??? backend/           # FastAPI API (app/, tests/)
??? database/          # SQL migrations V001?V008
??? docs/              # API contract and docs
```

---

## Prerequisites

- **Node.js** 18+ and npm 9+
- **Python** 3.11+
- Git

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/Prathmeshdongale/heatshield.git
cd heatshield
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux

npm run dev
```

App: http://localhost:5173

`frontend/.env` should contain:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `APP_ENV` | no | `development` | |
| `APP_HOST` | no | `0.0.0.0` | |
| `APP_PORT` | no | `8000` | |
| `SECRET_KEY` | prod | `change-me` | Change before deploy |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Comma-separated |
| `SUPABASE_URL` | live only | empty | Publishable / anon key project URL |
| `SUPABASE_PUBLISHABLE_KEY` | live only | empty | **Never** use the service-role key |
| `DEMO_MODE` | no | `true` | Set `false` when DB + ML are connected |
| `ML_MODEL_PATH` | live only | `../ml/artifacts/model.joblib` | Path to joblib artifact |

### Frontend (`frontend/.env`)

| Variable | Required | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | no | e.g. `http://localhost:8000/api/v1`. If unset, the UI uses synthetic demo data. |

**Never commit `.env` files.** Never put Supabase service-role keys or other secrets in the frontend.

---

## API overview

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/hospitals` | List hospitals + capacity / risk |
| `GET` | `/hospitals/{id}` | Hospital detail |
| `GET` | `/forecasts?hospital_id=&days=` | Demand forecast |
| `GET` | `/weather?hospital_id=&days=` | Weather observations |
| `GET` | `/alerts` | Active capacity-risk alerts |
| `GET` | `/metrics` | ML model evaluation metrics |

Full request/response shapes: [docs/api-contract.md](docs/api-contract.md).

---

## Database

PostgreSQL is hosted on Supabase. Migrations live in `database/migrations/` (`V001` ? `V008`). Apply them in order via the Supabase SQL editor, Supabase CLI, or `psql`.

See [database/README.md](database/README.md) for table summaries, RLS notes, and seed guidance. `V008` demo seed is for development/staging only.

When Supabase is not configured, repositories fall back to demo data automatically.

---

## Running tests

```bash
# Backend
cd backend
.\.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
pytest

# Frontend
cd frontend
npm run test
```

---

## Useful links (local)

| Resource | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000/api/v1 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Documentation

- [API contract](docs/api-contract.md)
- [Backend integration guide](backend/INTEGRATION.md)
- [Frontend setup](frontend/FRONTEND_SETUP.md)
- [Database layer](database/README.md)

---

## License

Add license information here.
