-- 4. MODELING & FORECASTS (Mart Layer)
-- DIM_RUNS (Tracking experiments)
CREATE TABLE dim_runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT,
    grain TEXT,
    -- 'weekly'
    horizon INTEGER,
    -- e.g. 8
    train_end_year_week INTEGER,
    model_family TEXT,
    -- 'prophet', 'xgb', ...
    params_json TEXT
);
-- FACT_FORECASTS_WEEKLY
CREATE TABLE fact_forecasts_weekly (
    run_id TEXT,
    year_week INTEGER,
    store_nbr INTEGER,
    family TEXT,
    horizon_step INTEGER,
    -- 1 to 8
    yhat_mean REAL,
    yhat_p10 REAL,
    yhat_p50 REAL,
    yhat_p90 REAL,
    PRIMARY KEY (run_id, year_week, store_nbr, family),
    FOREIGN KEY (run_id) REFERENCES dim_runs(run_id)
);
-- FACT_INVENTORY_DECISIONS_WEEKLY
CREATE TABLE fact_inventory_decisions_weekly (
    run_id TEXT,
    year_week INTEGER,
    store_nbr INTEGER,
    family TEXT,
    order_qty REAL,
    safety_stock REAL,
    service_level REAL,
    policy TEXT,
    PRIMARY KEY (run_id, year_week, store_nbr, family)
);
-- FACT_BACKTEST_METRICS
CREATE TABLE fact_backtest_metrics (
    run_id TEXT,
    metric_name TEXT,
    -- 'RMSE', 'WAPE'
    segment_type TEXT,
    -- 'global', 'store', 'family'
    segment_value TEXT,
    value REAL,
    n_obs INTEGER,
    FOREIGN KEY (run_id) REFERENCES dim_runs(run_id)
);
-- FACT_DRIFT_WEEKLY
CREATE TABLE fact_drift_weekly (
    run_id TEXT,
    year_week INTEGER,
    store_nbr INTEGER,
    family TEXT,
    drift_score REAL,
    flag_alert INTEGER
);