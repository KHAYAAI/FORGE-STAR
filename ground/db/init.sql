-- FORGE STAR telemetry schema (TimescaleDB). Data stays in SA (POPIA / sovereignty).
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS devices (
    device_id   TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,          -- pump, soil, collar, vessel, tracker
    customer    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS uplinks (
    time        TIMESTAMPTZ NOT NULL,
    device_id   TEXT NOT NULL,
    path        TEXT NOT NULL,          -- resale | satellite | ground | sim
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    payload     JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SELECT create_hypertable('uplinks', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS uplinks_device_time ON uplinks (device_id, time DESC);

-- Store-and-forward latency per hour: the number customers' SLAs are written against.
CREATE MATERIALIZED VIEW IF NOT EXISTS latency_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS bucket, path,
       count(*) AS messages,
       avg(extract(epoch FROM received_at - time)) AS avg_latency_s,
       max(extract(epoch FROM received_at - time)) AS max_latency_s
FROM uplinks GROUP BY bucket, path WITH NO DATA;
