-- =============================================================
-- HeatShield — Full Database Setup
-- Paste this entire file into Supabase SQL Editor and click RUN
-- =============================================================

-- ── Step 1: Enums ─────────────────────────────────────────────
DO $$ BEGIN
    CREATE TYPE data_status AS ENUM ('demo', 'historical', 'live');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_status AS ENUM ('green', 'amber', 'red', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ── Step 2: updated_at trigger function ───────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- ── Step 3: hospitals ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id    TEXT         PRIMARY KEY,
    name           TEXT         NOT NULL,
    region         TEXT         NOT NULL,
    address        TEXT         NOT NULL,
    latitude       NUMERIC(9,6) NOT NULL,
    longitude      NUMERIC(9,6) NOT NULL,
    contact_email  TEXT         NOT NULL,
    capacity_total INTEGER      NOT NULL CHECK (capacity_total > 0),
    data_status    data_status  NOT NULL DEFAULT 'demo',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS hospitals_updated_at ON hospitals;
CREATE TRIGGER hospitals_updated_at
    BEFORE UPDATE ON hospitals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_hospitals_region ON hospitals (region);

-- ── Step 4: hospital_capacity ─────────────────────────────────
CREATE TABLE IF NOT EXISTS hospital_capacity (
    id                 BIGSERIAL    PRIMARY KEY,
    hospital_id        TEXT         NOT NULL REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    recorded_date      DATE         NOT NULL,
    capacity_total     INTEGER      NOT NULL CHECK (capacity_total > 0),
    capacity_available INTEGER      NOT NULL CHECK (capacity_available >= 0),
    occupancy_pct      NUMERIC(5,2) NOT NULL CHECK (occupancy_pct BETWEEN 0 AND 200),
    risk_status        risk_status  NOT NULL,
    data_status        data_status  NOT NULL DEFAULT 'demo',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (hospital_id, recorded_date)
);

DROP TRIGGER IF EXISTS hospital_capacity_updated_at ON hospital_capacity;
CREATE TRIGGER hospital_capacity_updated_at
    BEFORE UPDATE ON hospital_capacity
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_hospital_capacity_hospital_date
    ON hospital_capacity (hospital_id, recorded_date DESC);

-- ── Step 5: weather_daily ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS weather_daily (
    id               BIGSERIAL    PRIMARY KEY,
    hospital_id      TEXT         NOT NULL REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    observation_date DATE         NOT NULL,
    temperature_max_c NUMERIC(5,2) NOT NULL,
    temperature_min_c NUMERIC(5,2) NOT NULL,
    humidity_pct     NUMERIC(5,2) NOT NULL CHECK (humidity_pct BETWEEN 0 AND 100),
    heat_index_c     NUMERIC(5,2),
    condition        TEXT,
    data_status      data_status  NOT NULL DEFAULT 'demo',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (hospital_id, observation_date),
    CHECK (temperature_min_c <= temperature_max_c)
);

DROP TRIGGER IF EXISTS weather_daily_updated_at ON weather_daily;
CREATE TRIGGER weather_daily_updated_at
    BEFORE UPDATE ON weather_daily
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_weather_hospital_date
    ON weather_daily (hospital_id, observation_date DESC);

-- ── Step 6: forecasts ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forecasts (
    id                   BIGSERIAL    PRIMARY KEY,
    hospital_id          TEXT         NOT NULL REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    forecast_date        DATE         NOT NULL,
    generated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    model_version        TEXT         NOT NULL,
    predicted_admissions NUMERIC(8,2) NOT NULL CHECK (predicted_admissions >= 0),
    confidence_lower     NUMERIC(8,2) NOT NULL CHECK (confidence_lower >= 0),
    confidence_upper     NUMERIC(8,2) NOT NULL CHECK (confidence_upper >= 0),
    risk_status          risk_status  NOT NULL,
    data_status          data_status  NOT NULL DEFAULT 'demo',
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (confidence_lower <= predicted_admissions),
    CHECK (predicted_admissions <= confidence_upper)
);

CREATE INDEX IF NOT EXISTS idx_forecasts_hospital_date
    ON forecasts (hospital_id, forecast_date ASC, generated_at DESC);

-- ── Step 7: model_metrics ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_metrics (
    id                 BIGSERIAL    PRIMARY KEY,
    model_version      TEXT         NOT NULL,
    evaluated_on       DATE         NOT NULL,
    mae                NUMERIC(8,4) NOT NULL CHECK (mae >= 0),
    rmse               NUMERIC(8,4) NOT NULL CHECK (rmse >= 0),
    r2                 NUMERIC(6,4) NOT NULL CHECK (r2 BETWEEN 0 AND 1),
    training_data_from DATE         NOT NULL,
    training_data_to   DATE         NOT NULL,
    feature_count      INTEGER      NOT NULL CHECK (feature_count > 0),
    data_status        data_status  NOT NULL DEFAULT 'demo',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (training_data_from < training_data_to),
    UNIQUE (model_version, evaluated_on)
);

CREATE INDEX IF NOT EXISTS idx_model_metrics_evaluated_on
    ON model_metrics (evaluated_on DESC);

-- ── Step 8: RLS — enable on all tables ────────────────────────
ALTER TABLE hospitals           ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospital_capacity   ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_daily       ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecasts           ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_metrics       ENABLE ROW LEVEL SECURITY;

-- Drop and recreate policies (safe to re-run)
DROP POLICY IF EXISTS "anon_read_hospitals"          ON hospitals;
DROP POLICY IF EXISTS "anon_read_hospital_capacity"  ON hospital_capacity;
DROP POLICY IF EXISTS "anon_read_weather_daily"      ON weather_daily;
DROP POLICY IF EXISTS "anon_read_forecasts"          ON forecasts;
DROP POLICY IF EXISTS "anon_read_model_metrics"      ON model_metrics;

CREATE POLICY "anon_read_hospitals"
    ON hospitals FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_hospital_capacity"
    ON hospital_capacity FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_weather_daily"
    ON weather_daily FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_forecasts"
    ON forecasts FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_model_metrics"
    ON model_metrics FOR SELECT TO anon USING (true);

-- ── Step 9: Seed demo data ────────────────────────────────────
INSERT INTO hospitals (hospital_id, name, region, address, latitude, longitude, contact_email, capacity_total, data_status)
VALUES
    ('H001', 'City General Hospital [DEMO]',      'Greater London',     '1 Demo Road, London, E1 1AA',          51.507400, -0.127800, 'ops@demo-citygen.nhs',    300, 'demo'),
    ('H002', 'Riverside Medical Centre [DEMO]',   'Greater London',     '22 River Lane, London, SE1 0BB',       51.499500, -0.115700, 'ops@demo-riverside.nhs',  180, 'demo'),
    ('H003', 'Northern District Hospital [DEMO]', 'Greater Manchester', '5 North Street, Manchester, M1 2CC',   53.480800, -2.242600, 'ops@demo-northern.nhs',   250, 'demo')
ON CONFLICT (hospital_id) DO NOTHING;

INSERT INTO hospital_capacity (hospital_id, recorded_date, capacity_total, capacity_available, occupancy_pct, risk_status, data_status)
VALUES
    ('H001', CURRENT_DATE-6, 300, 85, 71.67, 'amber', 'demo'),
    ('H001', CURRENT_DATE-5, 300, 80, 73.33, 'amber', 'demo'),
    ('H001', CURRENT_DATE-4, 300, 78, 74.00, 'amber', 'demo'),
    ('H001', CURRENT_DATE-3, 300, 75, 75.00, 'amber', 'demo'),
    ('H001', CURRENT_DATE-2, 300, 74, 75.33, 'amber', 'demo'),
    ('H001', CURRENT_DATE-1, 300, 73, 75.67, 'amber', 'demo'),
    ('H001', CURRENT_DATE,   300, 72, 76.00, 'amber', 'demo'),
    ('H002', CURRENT_DATE-6, 180, 25, 86.11, 'red',   'demo'),
    ('H002', CURRENT_DATE-5, 180, 22, 87.78, 'red',   'demo'),
    ('H002', CURRENT_DATE-4, 180, 20, 88.89, 'red',   'demo'),
    ('H002', CURRENT_DATE-3, 180, 18, 90.00, 'red',   'demo'),
    ('H002', CURRENT_DATE-2, 180, 17, 90.56, 'red',   'demo'),
    ('H002', CURRENT_DATE-1, 180, 16, 91.11, 'red',   'demo'),
    ('H002', CURRENT_DATE,   180, 15, 91.67, 'red',   'demo'),
    ('H003', CURRENT_DATE-6, 250,125, 50.00, 'green', 'demo'),
    ('H003', CURRENT_DATE-5, 250,122, 51.20, 'green', 'demo'),
    ('H003', CURRENT_DATE-4, 250,121, 51.60, 'green', 'demo'),
    ('H003', CURRENT_DATE-3, 250,122, 51.20, 'green', 'demo'),
    ('H003', CURRENT_DATE-2, 250,121, 51.60, 'green', 'demo'),
    ('H003', CURRENT_DATE-1, 250,120, 52.00, 'green', 'demo'),
    ('H003', CURRENT_DATE,   250,120, 52.00, 'green', 'demo')
ON CONFLICT (hospital_id, recorded_date) DO NOTHING;

INSERT INTO weather_daily (hospital_id, observation_date, temperature_max_c, temperature_min_c, humidity_pct, heat_index_c, condition, data_status)
VALUES
    ('H001', CURRENT_DATE-6, 34.2, 23.7, 65.0, 38.0, 'Heatwave', 'demo'),
    ('H001', CURRENT_DATE-5, 33.8, 23.3, 68.0, 37.8, 'Heatwave', 'demo'),
    ('H001', CURRENT_DATE-4, 36.1, 25.6, 65.0, 40.2, 'Heatwave', 'demo'),
    ('H001', CURRENT_DATE-3, 37.4, 26.9, 71.0, 42.1, 'Heatwave', 'demo'),
    ('H001', CURRENT_DATE-2, 35.9, 25.4, 68.0, 40.0, 'Heatwave', 'demo'),
    ('H001', CURRENT_DATE-1, 32.0, 21.5, 65.0, 35.5, 'Hot',      'demo'),
    ('H001', CURRENT_DATE,   30.5, 20.0, 65.0, 33.9, 'Hot',      'demo'),
    ('H002', CURRENT_DATE-6, 34.2, 23.7, 66.0, 38.1, 'Heatwave', 'demo'),
    ('H002', CURRENT_DATE-5, 33.8, 23.3, 69.0, 37.9, 'Heatwave', 'demo'),
    ('H002', CURRENT_DATE-4, 36.1, 25.6, 66.0, 40.3, 'Heatwave', 'demo'),
    ('H002', CURRENT_DATE-3, 37.4, 26.9, 72.0, 42.2, 'Heatwave', 'demo'),
    ('H002', CURRENT_DATE-2, 35.9, 25.4, 69.0, 40.1, 'Heatwave', 'demo'),
    ('H002', CURRENT_DATE-1, 32.0, 21.5, 66.0, 35.6, 'Hot',      'demo'),
    ('H002', CURRENT_DATE,   30.5, 20.0, 66.0, 34.0, 'Hot',      'demo'),
    ('H003', CURRENT_DATE-6, 28.0, 17.5, 55.0, 30.1, 'Warm',     'demo'),
    ('H003', CURRENT_DATE-5, 27.5, 17.0, 57.0, 29.8, 'Warm',     'demo'),
    ('H003', CURRENT_DATE-4, 29.0, 18.5, 55.0, 31.0, 'Warm',     'demo'),
    ('H003', CURRENT_DATE-3, 30.1, 19.6, 60.0, 32.5, 'Hot',      'demo'),
    ('H003', CURRENT_DATE-2, 29.5, 19.0, 58.0, 31.8, 'Hot',      'demo'),
    ('H003', CURRENT_DATE-1, 27.0, 16.5, 55.0, 29.2, 'Warm',     'demo'),
    ('H003', CURRENT_DATE,   26.5, 16.0, 55.0, 28.7, 'Warm',     'demo')
ON CONFLICT (hospital_id, observation_date) DO NOTHING;

INSERT INTO forecasts (hospital_id, forecast_date, model_version, predicted_admissions, confidence_lower, confidence_upper, risk_status, data_status)
VALUES
    ('H001', CURRENT_DATE+1, 'v1.2.0-demo', 42.5, 36.1, 48.9, 'amber',    'demo'),
    ('H001', CURRENT_DATE+2, 'v1.2.0-demo', 43.3, 36.8, 49.8, 'amber',    'demo'),
    ('H001', CURRENT_DATE+3, 'v1.2.0-demo', 44.1, 37.5, 50.7, 'amber',    'demo'),
    ('H001', CURRENT_DATE+4, 'v1.2.0-demo', 44.9, 38.2, 51.6, 'red',      'demo'),
    ('H001', CURRENT_DATE+5, 'v1.2.0-demo', 45.7, 38.8, 52.6, 'red',      'demo'),
    ('H001', CURRENT_DATE+6, 'v1.2.0-demo', 46.5, 39.5, 53.5, 'red',      'demo'),
    ('H001', CURRENT_DATE+7, 'v1.2.0-demo', 47.3, 40.2, 54.4, 'red',      'demo'),
    ('H002', CURRENT_DATE+1, 'v1.2.0-demo', 27.0, 23.0, 31.1, 'red',      'demo'),
    ('H002', CURRENT_DATE+2, 'v1.2.0-demo', 27.8, 23.6, 32.0, 'red',      'demo'),
    ('H002', CURRENT_DATE+3, 'v1.2.0-demo', 28.6, 24.3, 32.9, 'red',      'demo'),
    ('H002', CURRENT_DATE+4, 'v1.2.0-demo', 29.4, 25.0, 33.8, 'critical', 'demo'),
    ('H002', CURRENT_DATE+5, 'v1.2.0-demo', 30.2, 25.7, 34.7, 'critical', 'demo'),
    ('H002', CURRENT_DATE+6, 'v1.2.0-demo', 31.0, 26.4, 35.7, 'critical', 'demo'),
    ('H002', CURRENT_DATE+7, 'v1.2.0-demo', 31.8, 27.0, 36.6, 'critical', 'demo'),
    ('H003', CURRENT_DATE+1, 'v1.2.0-demo', 32.5, 27.6, 37.4, 'green',    'demo'),
    ('H003', CURRENT_DATE+2, 'v1.2.0-demo', 33.3, 28.3, 38.3, 'green',    'demo'),
    ('H003', CURRENT_DATE+3, 'v1.2.0-demo', 34.1, 29.0, 39.2, 'green',    'demo'),
    ('H003', CURRENT_DATE+4, 'v1.2.0-demo', 34.9, 29.7, 40.1, 'amber',    'demo'),
    ('H003', CURRENT_DATE+5, 'v1.2.0-demo', 35.7, 30.3, 41.1, 'amber',    'demo'),
    ('H003', CURRENT_DATE+6, 'v1.2.0-demo', 36.5, 31.0, 42.0, 'amber',    'demo'),
    ('H003', CURRENT_DATE+7, 'v1.2.0-demo', 37.3, 31.7, 42.9, 'amber',    'demo')
ON CONFLICT DO NOTHING;

INSERT INTO model_metrics (model_version, evaluated_on, mae, rmse, r2, training_data_from, training_data_to, feature_count, data_status)
VALUES ('v1.2.0-demo', '2026-10-01', 3.8, 5.1, 0.87, '2023-01-01', '2026-09-30', 12, 'demo')
ON CONFLICT (model_version, evaluated_on) DO NOTHING;

-- ── Verify ────────────────────────────────────────────────────
SELECT 'hospitals'        AS tbl, COUNT(*) FROM hospitals        UNION ALL
SELECT 'hospital_capacity',        COUNT(*) FROM hospital_capacity UNION ALL
SELECT 'weather_daily',            COUNT(*) FROM weather_daily     UNION ALL
SELECT 'forecasts',                COUNT(*) FROM forecasts         UNION ALL
SELECT 'model_metrics',            COUNT(*) FROM model_metrics;
