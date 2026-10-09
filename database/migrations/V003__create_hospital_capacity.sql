-- V003__create_hospital_capacity.sql
-- Daily snapshot of hospital bed capacity.
-- One row per hospital per recorded_date.
-- The API derives occupancy_pct and risk_status from these figures.

CREATE TABLE IF NOT EXISTS hospital_capacity (
    id                  BIGSERIAL   PRIMARY KEY,

    hospital_id         TEXT        NOT NULL
                                    REFERENCES hospitals (hospital_id)
                                    ON DELETE CASCADE,

    recorded_date       DATE        NOT NULL,

    capacity_total      INTEGER     NOT NULL CHECK (capacity_total > 0),
    capacity_available  INTEGER     NOT NULL CHECK (capacity_available >= 0),

    -- Stored as a computed convenience; can also be derived in queries.
    -- Must satisfy: occupancy_pct = ((total - available) / total) * 100
    occupancy_pct       NUMERIC(5,2) NOT NULL
                                    CHECK (occupancy_pct BETWEEN 0 AND 200),
                                    -- >100 is possible if overflow patients are counted

    risk_status         risk_status NOT NULL,

    data_status         data_status NOT NULL DEFAULT 'demo',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One snapshot per hospital per day
    UNIQUE (hospital_id, recorded_date)
);

CREATE TRIGGER hospital_capacity_updated_at
    BEFORE UPDATE ON hospital_capacity
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Most queries fetch the latest N days for a specific hospital
CREATE INDEX IF NOT EXISTS idx_hospital_capacity_hospital_date
    ON hospital_capacity (hospital_id, recorded_date DESC);

CREATE INDEX IF NOT EXISTS idx_hospital_capacity_date
    ON hospital_capacity (recorded_date DESC);

COMMENT ON TABLE  hospital_capacity                  IS 'Daily bed-capacity snapshots. One row per hospital per day.';
COMMENT ON COLUMN hospital_capacity.occupancy_pct    IS '((capacity_total - capacity_available) / capacity_total) * 100';
COMMENT ON COLUMN hospital_capacity.data_status      IS 'demo=synthetic | historical=loaded from source | live=real-time feed';
