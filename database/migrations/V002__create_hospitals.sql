-- V002__create_hospitals.sql
-- Master hospital registry. One row per physical hospital.
-- hospital_id is a short human-readable code (e.g. H001) used as the
-- shared identifier across all other tables AND the REST API.

CREATE TABLE IF NOT EXISTS hospitals (
    -- Primary key: short code aligned with API and mock_data.py
    hospital_id     TEXT        PRIMARY KEY
                                CHECK (hospital_id ~ '^H[0-9]{3,}$'),

    name            TEXT        NOT NULL,
    region          TEXT        NOT NULL,
    address         TEXT        NOT NULL,
    latitude        NUMERIC(9,6) NOT NULL
                                CHECK (latitude  BETWEEN -90  AND 90),
    longitude       NUMERIC(9,6) NOT NULL
                                CHECK (longitude BETWEEN -180 AND 180),
    contact_email   TEXT        NOT NULL
                                CHECK (contact_email LIKE '%@%'),
    capacity_total  INTEGER     NOT NULL CHECK (capacity_total > 0),

    -- Tracks whether this row is demo/synthetic or real
    data_status     data_status NOT NULL DEFAULT 'demo',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Keep updated_at current automatically
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER hospitals_updated_at
    BEFORE UPDATE ON hospitals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Useful for region-level queries
CREATE INDEX IF NOT EXISTS idx_hospitals_region
    ON hospitals (region);

COMMENT ON TABLE  hospitals                IS 'Master hospital registry. Rows with data_status=demo are synthetic.';
COMMENT ON COLUMN hospitals.hospital_id   IS 'Short code e.g. H001. Used as FK in all child tables and as the API identifier.';
COMMENT ON COLUMN hospitals.data_status   IS 'demo=synthetic seed | historical=real past data | live=real-time';
