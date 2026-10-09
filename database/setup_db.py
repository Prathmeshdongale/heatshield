"""
setup_db.py — Creates all tables and seeds demo data into Supabase.

HOW TO RUN:
    1. Get your secret key from:
       Supabase Dashboard → Project Settings → API → Project API Keys
       (It starts with sb_secret_... or is the legacy "service_role" JWT)

    2. Add it to backend/.env:
       SUPABASE_SECRET_KEY=sb_secret_xxxxxxxxxx

    3. Run:
       cd database
       python setup_db.py

The script uses the secret key to run DDL (CREATE TABLE etc.) via the
Supabase Management API, then seeds demo data via the REST API.
All tables use 'ON CONFLICT DO NOTHING' so reruns are safe.
"""

import sys
import os
import pathlib

# ── Load env from backend/.env ────────────────────────────────────────────────
env_path = pathlib.Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

SUPABASE_URL         = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_PUB_KEY     = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY  = os.environ.get("SUPABASE_SECRET_KEY", "")
# PAT (Personal Access Token) — for Supabase CLI and Management API
SUPABASE_ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
PROJECT_REF          = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "").strip("/")

if not SUPABASE_URL or not SUPABASE_PUB_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be set in backend/.env")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Use secret key for DDL, publishable key for DML reads
DDL_KEY = SUPABASE_SECRET_KEY or SUPABASE_PUB_KEY
DML_KEY = SUPABASE_PUB_KEY

REST_BASE = f"{SUPABASE_URL}/rest/v1"

DDL_HEADERS = {
    "apikey":        DDL_KEY,
    "Authorization": f"Bearer {DDL_KEY}",
    "Content-Type":  "application/json",
}

DML_HEADERS = {
    "apikey":        DML_KEY,
    "Authorization": f"Bearer {DML_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=ignore-duplicates,return=minimal",
}


# ── DDL via Supabase RPC or Management API ────────────────────────────────────

def run_ddl_via_rpc(sql: str, description: str) -> bool:
    """
    Execute arbitrary SQL using Supabase's rpc/exec_sql or pg_dump endpoints.
    Requires the secret key (service_role equivalent).
    """
    # Approach 1: POST /rest/v1/rpc/exec_sql (requires exec_sql function to exist)
    try:
        r = httpx.post(
            f"{REST_BASE}/rpc/exec_sql",
            headers=DDL_HEADERS,
            json={"sql": sql},
            timeout=30,
        )
        if r.status_code in (200, 201, 204):
            print(f"  ✓ {description}")
            return True
        # Might get 404 if function doesn't exist — try next approach
        if r.status_code != 404:
            print(f"  ✗ {description} — HTTP {r.status_code}: {r.text[:200]}")
            return False
    except Exception:
        pass

    # Approach 2: Supabase Management API (needs PAT/access_token, not project key)
    # This requires a personal access token — skip silently
    print(f"  ⚠ {description} — cannot run DDL with publishable key. Use the SQL Editor.")
    return False


FULL_SETUP_SQL = pathlib.Path(__file__).parent / "migrations" / "FULL_SETUP.sql"


def setup_schema():
    """
    Apply the full schema + seed via exec_sql RPC if available,
    otherwise guide the user to the SQL Editor.
    """
    print(f"\nConnecting to: {SUPABASE_URL}")
    print(f"Project ref:   {PROJECT_REF}")
    print(f"Secret key:    {'✓ present' if SUPABASE_SECRET_KEY else '✗ missing'}")
    print(f"Access token:  {'✓ present' if SUPABASE_ACCESS_TOKEN else '✗ missing'}\n")

    # Path A: Supabase CLI with PAT ──────────────────────────────────────────
    if SUPABASE_ACCESS_TOKEN and FULL_SETUP_SQL.exists():
        print("Trying Supabase CLI (npx supabase db query)...")
        import subprocess
        result = subprocess.run(
            ["npx", "--yes", "supabase", "db", "query",
             "--project-ref", PROJECT_REF,
             "--file", str(FULL_SETUP_SQL)],
            capture_output=True, text=True,
            env={**os.environ, "SUPABASE_ACCESS_TOKEN": SUPABASE_ACCESS_TOKEN},
            timeout=60,
        )
        if result.returncode == 0:
            print("  ✓ Schema applied via CLI")
            return True
        else:
            print(f"  ✗ CLI failed: {result.stderr[:300]}")

    # Path B: Management API db query endpoint ───────────────────────────────
    token = SUPABASE_ACCESS_TOKEN or SUPABASE_SECRET_KEY
    if token and FULL_SETUP_SQL.exists():
        print("Trying Management API db query...")
        sql = FULL_SETUP_SQL.read_text()
        try:
            r = httpx.post(
                f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"query": sql},
                timeout=60,
            )
            if r.status_code in (200, 201, 204):
                print("  ✓ Schema applied via Management API")
                return True
            else:
                print(f"  ✗ Management API: HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"  ✗ Management API error: {e}")

    # Path C: RPC exec_sql (requires secret key + pre-existing function) ─────
    if (SUPABASE_SECRET_KEY or SUPABASE_ACCESS_TOKEN) and FULL_SETUP_SQL.exists():
        sql = FULL_SETUP_SQL.read_text()
        success = run_ddl_via_rpc(sql, "Full schema + seed via RPC")
        if success:
            return True

    # No path worked — guide user ────────────────────────────────────────────
    print("=" * 60)
    print("  MANUAL SETUP REQUIRED")
    print("=" * 60)
    print(f"""
  To create the database tables, run the SQL manually:

  1. Open: https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new
  2. Paste the contents of: database/migrations/FULL_SETUP.sql
  3. Click "Run"

  OR add a Personal Access Token (PAT) to backend/.env:
     SUPABASE_ACCESS_TOKEN=sbp_xxxxxxxx
  (Get it from: https://supabase.com/dashboard/account/tokens)
  Then re-run this script.

  See database/README_SETUP.md for full instructions.
""")
    return False


def insert_demo_data():
    """
    Insert demo data row-by-row using the Supabase REST API.
    Uses the publishable key (SELECT-only RLS) — works if RLS INSERT is open,
    OR if the secret key is provided (bypasses RLS).
    """
    from datetime import date, timedelta

    today = date.today()
    headers = {
        "apikey":        DDL_KEY,
        "Authorization": f"Bearer {DDL_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=ignore-duplicates,return=minimal",
    }

    print("\nInserting demo data via REST API...\n")

    # ── hospitals ─────────────────────────────────────────────────────────────
    hospitals = [
        {
            "hospital_id": "H001", "name": "City General Hospital [DEMO]",
            "region": "Greater London", "address": "1 Demo Road, London, E1 1AA",
            "latitude": 51.5074, "longitude": -0.1278,
            "contact_email": "ops@demo-citygen.nhs", "capacity_total": 300,
            "data_status": "demo",
        },
        {
            "hospital_id": "H002", "name": "Riverside Medical Centre [DEMO]",
            "region": "Greater London", "address": "22 River Lane, London, SE1 0BB",
            "latitude": 51.4995, "longitude": -0.1157,
            "contact_email": "ops@demo-riverside.nhs", "capacity_total": 180,
            "data_status": "demo",
        },
        {
            "hospital_id": "H003", "name": "Northern District Hospital [DEMO]",
            "region": "Greater Manchester", "address": "5 North Street, Manchester, M1 2CC",
            "latitude": 53.4808, "longitude": -2.2426,
            "contact_email": "ops@demo-northern.nhs", "capacity_total": 250,
            "data_status": "demo",
        },
    ]
    r = httpx.post(f"{REST_BASE}/hospitals", headers=headers, json=hospitals, timeout=15)
    status = "✓" if r.status_code in (200, 201, 204) else f"✗ {r.text[:150]}"
    print(f"  hospitals:         HTTP {r.status_code} {status}")

    # ── hospital_capacity ─────────────────────────────────────────────────────
    capacity_rows = []
    cap_data = [
        ("H001", 300, [85,80,78,75,74,73,72], [71.67,73.33,74.00,75.00,75.33,75.67,76.00], "amber"),
        ("H002", 180, [25,22,20,18,17,16,15], [86.11,87.78,88.89,90.00,90.56,91.11,91.67], "red"),
        ("H003", 250, [125,122,121,122,121,120,120], [50.00,51.20,51.60,51.20,51.60,52.00,52.00], "green"),
    ]
    for hid, cap_total, avails, occs, risk in cap_data:
        for i, (av, occ) in enumerate(zip(avails, occs)):
            capacity_rows.append({
                "hospital_id": hid,
                "recorded_date": str(today - timedelta(days=6 - i)),
                "capacity_total": cap_total, "capacity_available": av,
                "occupancy_pct": occ, "risk_status": risk, "data_status": "demo",
            })
    r = httpx.post(f"{REST_BASE}/hospital_capacity", headers=headers, json=capacity_rows, timeout=15)
    status = "✓" if r.status_code in (200, 201, 204) else f"✗ {r.text[:150]}"
    print(f"  hospital_capacity: HTTP {r.status_code} {status}")

    # ── weather_daily ─────────────────────────────────────────────────────────
    weather_rows = []
    weather_data = {
        "H001": [(34.2,23.7,65.0,38.0,"Heatwave"),(33.8,23.3,68.0,37.8,"Heatwave"),
                 (36.1,25.6,65.0,40.2,"Heatwave"),(37.4,26.9,71.0,42.1,"Heatwave"),
                 (35.9,25.4,68.0,40.0,"Heatwave"),(32.0,21.5,65.0,35.5,"Hot"),(30.5,20.0,65.0,33.9,"Hot")],
        "H002": [(34.2,23.7,66.0,38.1,"Heatwave"),(33.8,23.3,69.0,37.9,"Heatwave"),
                 (36.1,25.6,66.0,40.3,"Heatwave"),(37.4,26.9,72.0,42.2,"Heatwave"),
                 (35.9,25.4,69.0,40.1,"Heatwave"),(32.0,21.5,66.0,35.6,"Hot"),(30.5,20.0,66.0,34.0,"Hot")],
        "H003": [(28.0,17.5,55.0,30.1,"Warm"),(27.5,17.0,57.0,29.8,"Warm"),
                 (29.0,18.5,55.0,31.0,"Warm"),(30.1,19.6,60.0,32.5,"Hot"),
                 (29.5,19.0,58.0,31.8,"Hot"),(27.0,16.5,55.0,29.2,"Warm"),(26.5,16.0,55.0,28.7,"Warm")],
    }
    for hid, obs_list in weather_data.items():
        for i, (tmax, tmin, hum, hi, cond) in enumerate(obs_list):
            weather_rows.append({
                "hospital_id": hid,
                "observation_date": str(today - timedelta(days=6 - i)),
                "temperature_max_c": tmax, "temperature_min_c": tmin,
                "humidity_pct": hum, "heat_index_c": hi,
                "condition": cond, "data_status": "demo",
            })
    r = httpx.post(f"{REST_BASE}/weather_daily", headers=headers, json=weather_rows, timeout=15)
    status = "✓" if r.status_code in (200, 201, 204) else f"✗ {r.text[:150]}"
    print(f"  weather_daily:     HTTP {r.status_code} {status}")

    # ── forecasts ─────────────────────────────────────────────────────────────
    forecast_rows = []
    forecast_data = [
        ("H001", [(42.5,36.1,48.9,"amber"),(43.3,36.8,49.8,"amber"),(44.1,37.5,50.7,"amber"),
                  (44.9,38.2,51.6,"red"),(45.7,38.8,52.6,"red"),(46.5,39.5,53.5,"red"),(47.3,40.2,54.4,"red")]),
        ("H002", [(27.0,23.0,31.1,"red"),(27.8,23.6,32.0,"red"),(28.6,24.3,32.9,"red"),
                  (29.4,25.0,33.8,"critical"),(30.2,25.7,34.7,"critical"),(31.0,26.4,35.7,"critical"),(31.8,27.0,36.6,"critical")]),
        ("H003", [(32.5,27.6,37.4,"green"),(33.3,28.3,38.3,"green"),(34.1,29.0,39.2,"green"),
                  (34.9,29.7,40.1,"amber"),(35.7,30.3,41.1,"amber"),(36.5,31.0,42.0,"amber"),(37.3,31.7,42.9,"amber")]),
    ]
    for hid, points in forecast_data:
        for i, (pred, lo, hi, risk) in enumerate(points):
            forecast_rows.append({
                "hospital_id": hid,
                "forecast_date": str(today + timedelta(days=i + 1)),
                "model_version": "v1.2.0-demo",
                "predicted_admissions": pred, "confidence_lower": lo, "confidence_upper": hi,
                "risk_status": risk, "data_status": "demo",
            })
    r = httpx.post(f"{REST_BASE}/forecasts", headers=headers, json=forecast_rows, timeout=15)
    status = "✓" if r.status_code in (200, 201, 204) else f"✗ {r.text[:150]}"
    print(f"  forecasts:         HTTP {r.status_code} {status}")

    # ── model_metrics ─────────────────────────────────────────────────────────
    r = httpx.post(
        f"{REST_BASE}/model_metrics",
        headers=headers,
        json=[{
            "model_version": "v1.2.0-demo", "evaluated_on": "2026-10-01",
            "mae": 3.8, "rmse": 5.1, "r2": 0.87,
            "training_data_from": "2023-01-01", "training_data_to": "2026-09-30",
            "feature_count": 12, "data_status": "demo",
        }],
        timeout=15,
    )
    status = "✓" if r.status_code in (200, 201, 204) else f"✗ {r.text[:150]}"
    print(f"  model_metrics:     HTTP {r.status_code} {status}")


def verify_data():
    """Read back row counts from each table."""
    print("\nVerifying data in Supabase...\n")
    # Use secret key for verification too (bypasses RLS)
    headers = {
        "apikey":        DDL_KEY,
        "Authorization": f"Bearer {DDL_KEY}",
    }
    tables = ["hospitals", "hospital_capacity", "weather_daily", "forecasts", "model_metrics"]
    all_ok = True
    for table in tables:
        try:
            r = httpx.get(f"{REST_BASE}/{table}?select=*", headers=headers, timeout=10)
            if r.status_code == 200:
                import json as _json
                rows = _json.loads(r.text)
                print(f"  ✓ {table:25s}: {len(rows):3d} row(s)")
            else:
                print(f"  ✗ {table:25s}: HTTP {r.status_code} — {r.text[:100]}")
                all_ok = False
        except Exception as e:
            print(f"  ✗ {table:25s}: {e}")
            all_ok = False
    return all_ok


if __name__ == "__main__":
    print("=" * 60)
    print("HeatShield — Supabase Database Setup")
    print("=" * 60)

    schema_ok = setup_schema()

    if not schema_ok:
        print(
            "\nSchema setup incomplete. After running FULL_SETUP.sql in the\n"
            "Supabase SQL Editor, you can re-run this script to verify the data.\n"
            "Or set SUPABASE_SECRET_KEY in backend/.env and rerun for auto-seeding.\n"
        )
        # Still try to verify (tables may exist from a previous run)
        print("Checking if tables already exist...\n")

    # Try to seed — this will only succeed if tables exist AND we have the right key
    insert_demo_data()
    ok = verify_data()

    if ok:
        print("\n✓ Database is ready. Restart the backend with DEMO_MODE=false\n")
    else:
        print("\n⚠ Some tables not found. See instructions above.\n")
