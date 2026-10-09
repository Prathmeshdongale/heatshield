# HeatShield — Supabase Database Setup

## Quick Setup (2 steps)

### Step 1 — Run the SQL in Supabase SQL Editor

1. Open: **https://supabase.com/dashboard/project/ehzqfftrhbvdklswicmj/sql/new**
2. Copy the entire contents of `database/migrations/FULL_SETUP.sql`
3. Paste it into the editor and click **Run**

This creates all tables, enables RLS, and seeds 3 demo hospitals with 7 days of
weather, capacity, and forecast data.

### Step 2 — Add your secret key and re-seed (optional, for automation)

1. In the Supabase dashboard go to:  
   **Project Settings → API → Project API Keys**
2. Copy the **Secret** key (starts with `sb_secret_...`)
3. Add it to `backend/.env`:
   ```
   SUPABASE_SECRET_KEY=sb_secret_xxxxxxxxxx
   ```
4. Run `python setup_db.py` from the `database/` folder to verify and re-seed.

---

## After Setup

The backend will automatically switch from demo data to live Supabase data.
Make sure `backend/.env` has:
```
DEMO_MODE=false
SUPABASE_URL=https://ehzqfftrhbvdklswicmj.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_vO2N8JIMCjkugXlXcRwzeQ_GYgfnKLI
```

Restart the backend after running the SQL:
```
cd backend
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open the frontend at **http://localhost:5173** — the dashboard will show
live data from Supabase instead of the demo fallback.

---

## What gets created

| Table              | Demo rows |
|--------------------|-----------|
| hospitals          | 3         |
| hospital_capacity  | 21 (7 days × 3) |
| weather_daily      | 21 (7 days × 3) |
| forecasts          | 21 (7 days × 3) |
| model_metrics      | 1         |

All rows are tagged `data_status = 'demo'`.

---

## Alternative: Supabase CLI

If you have a Supabase Personal Access Token (PAT):

```powershell
# Set the access token
$env:SUPABASE_ACCESS_TOKEN = "sbp_xxxxxxxx"

# Run the SQL against the remote project
npx supabase db query --project-ref ehzqfftrhbvdklswicmj `
  --file database/migrations/FULL_SETUP.sql
```
