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
    path        TEXT NOT NULL,          -- resale | satellite | ground
    sat         INTEGER,                -- satellite that carried it (store-and-forward)
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

SELECT add_continuous_aggregate_policy('latency_hourly',
    start_offset => INTERVAL '3 days', end_offset => INTERVAL '1 minute', schedule_interval => INTERVAL '5 minutes');

-- Latency percentiles by path: what an SLA ("95% within X minutes") is written against.
CREATE OR REPLACE VIEW latency_sla AS
SELECT path, count(*) AS messages,
       percentile_cont(0.5)  WITHIN GROUP (ORDER BY extract(epoch FROM received_at - time)) / 60 AS p50_min,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM received_at - time)) / 60 AS p95_min,
       max(extract(epoch FROM received_at - time)) / 60 AS max_min
FROM uplinks WHERE time > now() - INTERVAL '7 days' GROUP BY path;


-- POPIA: keep raw device messages for 24 months by default (per-customer exceptions in contracts)
SELECT add_retention_policy('uplinks', INTERVAL '24 months', if_not_exists => TRUE);

-- Commercial: customer plans and monthly invoices (ground/billing/billing.py)
CREATE TABLE IF NOT EXISTS customer_plans (
    customer        TEXT PRIMARY KEY,
    price_per_device NUMERIC NOT NULL DEFAULT 3.50,   -- USD per active device per month
    min_monthly     NUMERIC NOT NULL DEFAULT 0,
    sla_p95_min     NUMERIC NOT NULL DEFAULT 60,      -- 95% of satellite messages within this many minutes
    sla_credit_pct  NUMERIC NOT NULL DEFAULT 10,      -- credit if the SLA is missed
    currency        TEXT NOT NULL DEFAULT 'USD'
);
CREATE TABLE IF NOT EXISTS invoices (
    customer TEXT NOT NULL, month TEXT NOT NULL, active_devices INT NOT NULL, messages BIGINT NOT NULL,
    sla_p95_min NUMERIC, sla_met BOOLEAN, subtotal NUMERIC NOT NULL, credit NUMERIC NOT NULL, total NUMERIC NOT NULL,
    currency TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY (customer, month)
);