-- V006__create_model_metrics.sql
-- ML model evaluation metrics — one row per training/evaluation run.
-- The GET /api/v1/metrics endpoint returns the row with the highest evaluated_on.

CREATE TABLE IF NOT EXISTS model_metrics (
    id                  BIGSERIAL   PRIMARY KEY,

    -- Matches ForecastResponse.model_version
    model_version       TEXT        NOT NULL,

    evaluated_on        DATE        NOT NULL,

    -- Mean Absolute Error (admissions / day)
    mae                 NUMERIC(8,4) NOT NULL CHECK (mae >= 0),

    -- Root Mean Square Error
    rmse                NUMERIC(8,4) NOT NULL CHECK (rmse >= 0),

    -- R-squared (coefficient of determination) — must be in [0, 1]
    r2                  NUMERIC(6,4) NOT NULL CHECK (r2 BETWEEN 0 AND 1),

    training_data_from  DATE        NOT NULL,
    training_data_to    DATE        NOT NULL,

    feature_count       INTEGER     NOT NULL CHECK (feature_count > 0),

    data_status         data_status NOT NULL DEFAULT 'demo',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (training_data_from < training_data_to),
    -- One evaluation record per version per day
    UNIQUE (model_version, evaluated_on)
);

CREATE INDEX IF NOT EXISTS idx_model_metrics_evaluated_on
    ON model_metrics (evaluated_on DESC);

COMMENT ON TABLE  model_metrics              IS 'ML model evaluation metrics. Latest row by evaluated_on is current.';
COMMENT ON COLUMN model_metrics.mae          IS 'Mean Absolute Error in predicted admissions per day.';
COMMENT ON COLUMN model_metrics.r2           IS 'R-squared score; higher is better, max 1.0.';
COMMENT ON COLUMN model_metrics.data_status  IS 'demo=synthetic | live=real evaluation run';
