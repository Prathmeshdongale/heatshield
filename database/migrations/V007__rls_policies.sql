-- V007__rls_policies.sql
-- Row Level Security (RLS) policies.
--
-- Access model:
--   anon role   → the publishable/anon key used by the backend (never the frontend directly)
--   service_role → Supabase service role; used ONLY for migrations and seeding (never exposed)
--
-- All tables are READ-ONLY for the anon role.
-- INSERT / UPDATE / DELETE require the service_role (applied via Supabase dashboard
-- or a trusted server-side process — never from the frontend or from user-facing API routes).
--
-- IMPORTANT: The service-role key must NEVER appear in:
--   - frontend code
--   - .env files committed to Git
--   - API responses
--   Use it only in Supabase migrations / trusted backend scripts.

-- ── Enable RLS on every table ────────────────────────────────────────────────
ALTER TABLE hospitals           ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospital_capacity   ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_daily       ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecasts           ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_metrics       ENABLE ROW LEVEL SECURITY;

-- ── hospitals ─────────────────────────────────────────────────────────────────
-- anon can SELECT all hospitals (list and detail endpoints)
CREATE POLICY "anon_read_hospitals"
    ON hospitals
    FOR SELECT
    TO anon
    USING (true);

-- ── hospital_capacity ────────────────────────────────────────────────────────
CREATE POLICY "anon_read_hospital_capacity"
    ON hospital_capacity
    FOR SELECT
    TO anon
    USING (true);

-- ── weather_daily ────────────────────────────────────────────────────────────
CREATE POLICY "anon_read_weather_daily"
    ON weather_daily
    FOR SELECT
    TO anon
    USING (true);

-- ── forecasts ────────────────────────────────────────────────────────────────
CREATE POLICY "anon_read_forecasts"
    ON forecasts
    FOR SELECT
    TO anon
    USING (true);

-- ── model_metrics ────────────────────────────────────────────────────────────
CREATE POLICY "anon_read_model_metrics"
    ON model_metrics
    FOR SELECT
    TO anon
    USING (true);

-- ── Notes for future auth extension ──────────────────────────────────────────
-- If per-hospital write access is added later, add policies like:
--
--   CREATE POLICY "authenticated_insert_forecasts"
--       ON forecasts FOR INSERT
--       TO authenticated
--       WITH CHECK (auth.role() = 'service_role');
--
-- Always test with: SELECT * FROM pg_policies WHERE tablename = '<table>';
