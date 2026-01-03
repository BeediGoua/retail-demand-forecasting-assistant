-- 0. CLEANUP
DROP TABLE IF EXISTS fact_drift_weekly;
DROP TABLE IF EXISTS fact_backtest_metrics;
DROP TABLE IF EXISTS fact_inventory_decisions_weekly;
DROP TABLE IF EXISTS fact_forecasts_weekly;
DROP TABLE IF EXISTS dim_runs;
DROP TABLE IF EXISTS fact_sales_weekly;
DROP TABLE IF EXISTS fact_sales_daily;
DROP TABLE IF EXISTS bridge_event_store_day;
DROP TABLE IF EXISTS dim_week;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_family;
DROP TABLE IF EXISTS dim_store;