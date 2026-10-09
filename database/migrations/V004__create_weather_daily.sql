-- V004__create_weather_daily.sql
-- Daily weather observations associated with a hospital's region.
-- One row per hospital per observation_date.
-- heat_index_c is the "feels like" temperature (temperature + humidity effect).

CREATE TABLE IF NOT EXISTS weather_daily (
    id                  BIGSERIAL   PRIMARY KEY,

    hospital_id         TEXT        NOT NULL
                                    REFERENCES hospitals (hospital_id)
                                    ON DELETE CASCADE,

    observation_date    DATE        NOT NULL,

    temperature_max_c   NUMERIC(5,2) NOT NULL,
    temperature_min_c   NUMERIC(5,2) NOT NULL,

    -- Humidity as a percentage (0–100)
    humidity_pct        NUMERIC(5,2) NOT NULL
                                    CHECK (humidity_pct BETWEEN 0 AND 100),

    -- Apparent temperature combining heat and humidity
    heat_index_c        NUMERIC(5,2),

    -- Free-text condition label e.g. "Heatwave", "Hot", "Warm"
    condition           TEXT,

    data_status         data_status NOT NULL DEFAULT 'demo',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (hospital_id, observation_date),
    CHECK (temperature_min_c <= temperature_max_c)
);

CREATE TRIGGER weather_daily_updated_at
    BEFORE UPDATE ON weather_daily
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_weather_hospital_date
    ON weather_daily (hospital_id, observation_date DESC);

CREATE INDEX IF NOT EXISTS idx_weather_date
    ON weather_daily (observation_date DESC);

-- Useful for heatwave-detection queries across all hospitals
CREATE INDEX IF NOT EXISTS idx_weather_heat_index
    ON weather_daily (heat_index_c DESC)
    WHERE heat_index_c IS NOT NULL;

COMMENT ON TABLE  weather_daily               IS 'Daily weather observations per hospital region.';
COMMENT ON COLUMN weather_daily.heat_index_c  IS 'Apparent temperature (°C) combining air temperature and humidity.';
COMMENT ON COLUMN weather_daily.data_status   IS 'demo=synthetic | historical=loaded | live=real-time feed';
