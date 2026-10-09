-- V005__create_forecasts.sql
-- ML-model demand forecasts. One row per hospital per forecast_date per model run.
-- A "run" is identified by (hospital_id, generated_at, model_version).
-- Multiple runs may exist for the same forecast_date; the API fetches the latest.

CREATE TABLE IF NOT EXISTS forecasts (
    id                      BIGSERIAL   PRIMARY KEY,

    hospital_id             TEXT        NOT NULL
                                        REFERENCES hospitals (hospital_id)
                                        ON DELETE CASCADE,

    -- The calendar date this prediction is FOR (not when it was made)
    forecast_date           DATE        NOT NULL,

    -- When the model produced this row
    generated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Matches ModelMetrics.model_version — must be consistent
    model_version           TEXT        NOT NULL,

    predicted_admissions    NUMERIC(8,2) NOT NULL CHECK (predicted_admissions >= 0),
    confidence_lower        NUMERIC(8,2) NOT NULL CHECK (confidence_lower >= 0),
    confidence_upper        NUMERIC(8,2) NOT NULL CHECK (confidence_upper >= 0),

    risk_status             risk_status NOT NULL,

    data_status             data_status NOT NULL DEFAULT 'demo',

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (confidence_lower <= predicted_admissions),
    CHECK (predicted_admissions <= confidence_upper)
);

-- Primary query pattern: latest forecast for a hospital over N future days
CREATE INDEX IF NOT EXISTS idx_forecasts_hospital_date
    ON forecasts (hospital_id, forecast_date ASC, generated_at DESC);

-- Useful for model-version filtering
CREATE INDEX IF NOT EXISTS idx_forecasts_model_version
    ON forecasts (model_version, generated_at DESC);

COMMENT ON TABLE  forecasts               IS 'ML demand forecasts. Fetch latest generated_at per (hospital_id, forecast_date).';
COMMENT ON COLUMN forecasts.forecast_date IS 'Calendar date the prediction applies to.';
COMMENT ON COLUMN forecasts.generated_at  IS 'Timestamp the ML pipeline produced this row.';
COMMENT ON COLUMN forecasts.data_status   IS 'demo=synthetic | live=model output';
