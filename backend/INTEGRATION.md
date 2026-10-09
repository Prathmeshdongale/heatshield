# HeatShield Backend — Integration Report

## Test results

```
120 passed, 0 failed, 3 warnings (third-party deprecations only)
Python 3.12 / pytest 8.2.0 / platform win32
```

### Coverage by test file

| File | Tests | What is covered |
|---|---|---|
| test_health.py | 2 | GET /health — 200, body fields |
| test_hospitals.py | 9 | List + detail, 404, case-insensitive ID |
| test_forecasts.py | 9 | 200, day counts, fields, 404, 422 (days=0, days=15, missing param) |
| test_weather.py | 7 | 200, day counts, fields, 404, 422 |
| test_alerts.py | 7 | All alerts, filter, empty filter, meta count, demo label |
| test_metrics.py | 4 | 200, fields, r2 range, demo label |
| test_capacity_service.py | 11 | Demo + live mode, risk recalculation from occupancy |
| test_forecast_service.py | 14 | Demo, live happy path, 4 explicit model-failure → 503 assertions |
| test_alert_service.py | 9 | red/critical → alert, green → no alert, severity mapping, DB error resilience |
| test_ml_adapter.py | 14 | load, predict (3-col, 1-col, negatives), errors, feature order |
| test_risk.py | 17 | All threshold boundaries, unknown when capacity=None/0/<0 |
| test_db_schema.py | 15 | Repository fallback, field shapes, mock-data consistency |

---

## API contract verification

Every endpoint matches `docs/api-contract.md`.

| Endpoint | Status | HTTP codes verified |
|---|---|---|
| GET /api/v1/health | ✓ | 200 |
| GET /api/v1/hospitals | ✓ | 200 |
| GET /api/v1/hospitals/{id} | ✓ | 200, 404 |
| GET /api/v1/forecasts | ✓ | 200, 404, 422 |
| GET /api/v1/weather | ✓ | 200, 404, 422 |
| GET /api/v1/alerts | ✓ | 200 |
| GET /api/v1/metrics | ✓ | 200 |

All responses carry `status.data_source` (`"demo"` or `"live"`) and a `note` field.  
Demo responses include `[DEMO]` in hospital names.  
Error bodies follow `{ "detail": { "error": "...", "code": "..." } }`.

---

## API documentation

Start the server, then open:

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## CORS

Configured in `app/main.py` via `CORSMiddleware`.  
Allowed origin is read from `CORS_ORIGINS` in `.env` — defaults to `http://localhost:5173` (Vite dev server).  
To allow multiple origins: `CORS_ORIGINS=http://localhost:5173,https://your-production-domain.com`

---

## Environment variables

Copy `backend/.env.example` to `backend/.env` and fill in values.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `APP_ENV` | no | `development` | |
| `APP_HOST` | no | `0.0.0.0` | |
| `APP_PORT` | no | `8000` | |
| `SECRET_KEY` | yes in prod | `change-me` | Change before deploying |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Comma-separated |
| `SUPABASE_URL` | for live | `""` | Publishable only |
| `SUPABASE_PUBLISHABLE_KEY` | for live | `""` | Publishable only |
| `DEMO_MODE` | no | `true` | Set `false` to use DB + ML |
| `ML_MODEL_PATH` | for live | `../ml/artifacts/model.joblib` | joblib artifact from ML team |

**Never commit `.env` to Git.** It is listed in `.gitignore`.  
**Never use the Supabase service-role key** in `SUPABASE_PUBLISHABLE_KEY` or any backend config.

---

## Secrets audit

- No real credentials in any committed file — confirmed by grep scan.
- `.env.example` uses placeholder values only (`your-project.supabase.co`, `sb_publishable_xxxxxx`).
- `.gitignore` covers `.env`, `.env.*`, `.venv/`, `__pycache__/`, `*.joblib`, `*.pkl`.
- Git history contains one commit on `feature/backend-api` — no secrets ever committed.

---

## Running migrations

```bash
# Option A — Supabase SQL Editor (recommended for first-time setup)
# Paste each file in order V001 → V008 into the SQL Editor in your Supabase project.

# Option B — psql (replace placeholders with your project connection string)
PGPASSWORD=<db-password> psql \
  "postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres" \
  -f database/migrations/V001__create_enums.sql \
  -f database/migrations/V002__create_hospitals.sql \
  -f database/migrations/V003__create_hospital_capacity.sql \
  -f database/migrations/V004__create_weather_daily.sql \
  -f database/migrations/V005__create_forecasts.sql \
  -f database/migrations/V006__create_model_metrics.sql \
  -f database/migrations/V007__rls_policies.sql \
  -f database/migrations/V008__demo_seed.sql   # dev/staging only
```

V008 is the demo seed — only apply it in dev/staging, not production.

---

## Starting the backend

```bash
# From the repo root
cd backend

# Create and activate virtual environment (first time only)
python -m venv .venv
source .venv/Scripts/activate   # Windows bash
# or: .venv\Scripts\activate.bat  (CMD)
# or: .venv/Scripts/Activate.ps1  (PowerShell)

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env — set SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY if connecting to DB

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests (separate terminal)
pytest
```

---

## curl examples

All examples use demo data (DEMO_MODE=true, no DB required).

### Health check
```bash
curl http://localhost:8000/api/v1/health
```
```json
{ "status": "ok", "env": "development", "version": "1.0.0" }
```

### List hospitals
```bash
curl http://localhost:8000/api/v1/hospitals
```
```json
{
  "data": [
    {
      "hospital_id": "H001",
      "name": "City General Hospital [DEMO]",
      "region": "Greater London",
      "capacity_total": 300,
      "capacity_available": 72,
      "occupancy_pct": 76.0,
      "risk_status": "amber"
    }
  ],
  "meta": { "count": 3, "page": 1, "page_size": 3 },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### Hospital detail
```bash
curl http://localhost:8000/api/v1/hospitals/H001
```
```json
{
  "data": {
    "hospital_id": "H001",
    "name": "City General Hospital [DEMO]",
    "region": "Greater London",
    "address": "1 Demo Road, London, E1 1AA",
    "latitude": 51.5074,
    "longitude": -0.1278,
    "contact_email": "ops@demo-citygen.nhs",
    "capacity_total": 300,
    "capacity_available": 72,
    "occupancy_pct": 76.0,
    "risk_status": "amber"
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### Hospital not found (404)
```bash
curl http://localhost:8000/api/v1/hospitals/ZZZZ
```
```json
{ "detail": { "error": "Hospital 'ZZZZ' not found", "code": "HOSPITAL_NOT_FOUND" } }
```

### Demand forecast
```bash
curl "http://localhost:8000/api/v1/forecasts?hospital_id=H001&days=3"
```
```json
{
  "data": {
    "hospital_id": "H001",
    "model_version": "v1.2.0-demo",
    "generated_at": "2026-10-09T08:00:00+00:00",
    "days_requested": 3,
    "points": [
      { "forecast_date": "2026-10-10", "predicted_admissions": 42.5, "confidence_lower": 36.1, "confidence_upper": 48.9, "risk_status": "amber" },
      { "forecast_date": "2026-10-11", "predicted_admissions": 43.3, "confidence_lower": 36.8, "confidence_upper": 49.8, "risk_status": "amber" },
      { "forecast_date": "2026-10-12", "predicted_admissions": 44.1, "confidence_lower": 37.5, "confidence_upper": 50.7, "risk_status": "amber" }
    ]
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### Forecast validation error (422)
```bash
curl "http://localhost:8000/api/v1/forecasts?hospital_id=H001&days=0"
```
```json
{ "detail": [{ "type": "greater_than_equal", "loc": ["query", "days"], "msg": "Input should be greater than or equal to 1" }] }
```

### Weather observations
```bash
curl "http://localhost:8000/api/v1/weather?hospital_id=H002&days=2"
```
```json
{
  "data": {
    "hospital_id": "H002",
    "days_requested": 2,
    "observations": [
      { "observation_date": "2026-10-08", "temperature_max_c": 37.4, "temperature_min_c": 26.9, "humidity_pct": 71.0, "heat_index_c": 41.2, "condition": "Heatwave" },
      { "observation_date": "2026-10-09", "temperature_max_c": 35.9, "temperature_min_c": 25.4, "humidity_pct": 68.0, "heat_index_c": 39.7, "condition": "Heatwave" }
    ]
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### Active alerts
```bash
curl "http://localhost:8000/api/v1/alerts?hospital_id=H002"
```
```json
{
  "data": [
    {
      "alert_id": "ALT-0042",
      "hospital_id": "H002",
      "hospital_name": "Riverside Medical Centre [DEMO]",
      "severity": "high",
      "message": "DEMO: Predicted admissions exceed 85% capacity on 2026-10-12",
      "triggered_at": "2026-10-09T06:05:00+00:00",
      "forecast_date": "2026-10-12",
      "resolved": false
    }
  ],
  "meta": { "count": 1, "page": 1, "page_size": 1 },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

### ML metrics
```bash
curl http://localhost:8000/api/v1/metrics
```
```json
{
  "data": {
    "model_version": "v1.2.0-demo",
    "evaluated_on": "2026-10-01",
    "mae": 3.8,
    "rmse": 5.1,
    "r2": 0.87,
    "training_data_from": "2023-01-01",
    "training_data_to": "2026-09-30",
    "feature_count": 12
  },
  "status": { "data_source": "demo", "note": "DEMO DATA — not real hospital information" }
}
```

---

## Git commands to push and open a PR

```bash
# Push the backend branch
git push -u origin feature/backend-api

# Open a pull request (GitHub CLI)
gh pr create \
  --base main \
  --head feature/backend-api \
  --title "feat(backend): FastAPI backend with services, DB migrations and 120 tests" \
  --body "$(cat <<'EOF'
## Summary
Complete FastAPI backend for HeatShield including:
- 7 REST endpoints matching the agreed API contract
- Full service/repository/integration layer separation
- ML adapter with typed interface contract for Member 2
- Supabase DB integration with RLS + graceful demo-mode fallback
- 8 SQL migration files (V001–V008)
- 120 tests, 0 failures, no live credentials required

## What was tested
- All route handlers (200, 404, 422, 503)
- Service layer: demo + live mode, model failure → 503 not silent substitution
- ML adapter: load, predict, error cases, feature order
- Risk thresholds: all boundary conditions
- Repository fallback: DB unavailable → demo data

## Dependencies on other members
- **Member 1 (Frontend):** consume `status.data_source` to show demo banner; handle 503 on `/forecasts`
- **Member 2 (ML):** place joblib artifact at `ML_MODEL_PATH`; confirm `MLFeatures` field names and output shape `[pred, lower, upper]`
- **DB owner:** apply migrations V001–V008 in order; confirm `hospital_id` format matches `H\d{3,}`

## Files changed
63 files — backend/app/, backend/tests/, database/migrations/, docs/api-contract.md, .gitignore

## No secrets committed
Verified by grep scan. .env excluded by .gitignore.
EOF
)"
```

---

## Cross-team handoff checklist

### For Member 1 (Frontend)
- Base URL: `http://localhost:8000/api/v1`
- Check `response.status.data_source === "demo"` → show demo banner
- Handle HTTP 503 on `/forecasts` → show "Forecast unavailable" state, not a blank chart
- Hospital IDs: `H001`, `H002`, `H003` in demo mode
- All list responses have `meta.count`

### For Member 2 (ML team)
- Place trained artifact at path in `ML_MODEL_PATH` (default: `../ml/artifacts/model.joblib`)
- Model must expose `model.predict(X)` where `X` is a list of feature lists
- Feature order (must match `MLFeatures.to_list()`):
  1. temperature_max_c
  2. temperature_min_c
  3. humidity_pct
  4. heat_index_c
  5. occupancy_pct
  6. capacity_total
  7. day_of_week (0=Mon)
  8. month (1–12)
- Output: `[[predicted_admissions, confidence_lower, confidence_upper]]` per row
- Optionally expose `model.version` attribute for traceability
- After adding the artifact, set `DEMO_MODE=false` and restart the server

### For DB owner
- Apply migrations V001–V008 in order (see `database/README.md`)
- V008 demo seed is optional — dev/staging only
- Verify RLS: `SELECT tablename, policyname FROM pg_policies ORDER BY tablename;`
- hospital_id format must match `H\d{3,}` (e.g. H001, H002)
