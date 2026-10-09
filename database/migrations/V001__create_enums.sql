-- V001__create_enums.sql
-- Shared enum types used across multiple tables.
-- Run before any table migrations.

-- data_status distinguishes the origin/reliability of a row.
--   demo       → synthetic seed data, clearly not real
--   historical → real past observations loaded from external source
--   live       → produced in real-time by connected systems
DO $$ BEGIN
    CREATE TYPE data_status AS ENUM ('demo', 'historical', 'live');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- risk_status matches the RiskStatus enum in backend/app/schemas/hospital.py
DO $$ BEGIN
    CREATE TYPE risk_status AS ENUM ('green', 'amber', 'red', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- alert_severity matches AlertSeverity in backend/app/schemas/alert.py
DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
