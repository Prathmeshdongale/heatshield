# HeatShield — Database Layer

## Overview

PostgreSQL hosted on Supabase. All access from the backend uses the
**publishable (anon) key only**. The service-role key is used exclusively
for running migrations and is never stored in Git or exposed to the frontend.

---

## Table summary

| Table | Purpose | PK |
|---|---|---|
| `hospitals` | Master hospital registry | `hospital_id` (TEXT, e.g. H001) |
| `hospital_capacity` | Daily bed-capacity snapshots | `id` BIGSERIAL |
| `weather_daily` | Daily weather observations per hospital region | `id` BIGSERIAL |
| `forecasts` | ML demand forecasts (one row per hospital per forecast date per run) | `id` BIGSERIAL |
| `model_metrics` | ML evaluation metrics per training run | `id` BIGSERIAL |

All tables carry a `data_status` column:

| Value | Meaning |
|---|---|
| `demo` | Synthetic seed data — clearly not real |
| `historical` | Real past data loaded from an external source |
| `live` | Real-time data from a connected system |

---

## Applying migrations

Migrations are plain SQL files prefixed `V<NNN>__<description>.sql`.
Apply them **in order** using the Supabase SQL editor or the Supabase CLI.

### Option A — Supabase dashboard SQL editor

1. Open your project → SQL Editor.
2. Paste and run each file in order: V001 → V002 → … → V008.
3. V008 (demo seed) is optional for production.

### Option B — Supabase CLI

```bash
# Install CLI
npm install -g supabase

# Link to your project (requires service-role key — keep it local)
supabase login
supabase link --project-ref <your-project-ref>

# Push migrations (CLI reads from supabase/migrations/ by default;
# copy or symlink database/migrations/ there, or run files manually)
supabase db push
```

### Option C — psql (direct connection)

```bash
# Connection string is in your Supabase project → Settings → Database
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

---

## Environment variables

Backend `.env` (never committed to Git — copy from `.env.example`):

```dotenv
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxxxx
```

**Never add `SUPABASE_SERVICE_ROLE_KEY` to `.env` or any file tracked by Git.**
Use it only in the Supabase dashboard or a secure CI/CD secrets store.

---

## Row Level Security

V007 enables RLS on all tables. The `anon` role (used by the backend's
publishable key) has SELECT-only access. INSERT/UPDATE/DELETE require the
`service_role`, which is only available server-side.

To verify policies are active:
```sql
SELECT tablename, policyname, roles, cmd
FROM pg_policies
ORDER BY tablename;
```

---

## Backend behaviour when the database is unavailable

The backend is designed to degrade gracefully:

1. If `SUPABASE_URL` or `SUPABASE_PUBLISHABLE_KEY` are empty, the Supabase
   client is not initialised. A warning is logged at startup.
2. If the client fails to initialise (network error, bad credentials), the
   error is caught and logged. The client is set to `None`.
3. All repository functions check `get_supabase() is None` before any query.
   When `None`, they return demo data from `mock_data.py` immediately.
4. If a query raises an exception (timeout, RLS denial, schema mismatch),
   the repository catches it, logs the error, and returns demo data.
5. The `/health` endpoint does **not** check DB connectivity — it reflects
   only whether the FastAPI process is running. A separate DB health check
   can be added later at `/api/v1/health/db`.
6. All responses include `status.data_source` so the frontend can display
   a "demo data" banner when the DB is not feeding live data.

---

## Adding real data

When connecting a real data feed:

1. Insert rows with `data_status = 'historical'` or `'live'`.
2. The repositories will return those rows automatically.
3. Remove `data_status = 'demo'` filter if you want both demo and live rows
   blended — or add a filter in the repository to exclude demo rows in production.

---

## Running DB-related tests (no live DB needed)

```bash
cd backend
pytest tests/test_db_schema.py -v
```

These tests patch `get_supabase()` to return `None` and verify the fallback
behaviour and mock-data consistency — no Supabase credentials required.
