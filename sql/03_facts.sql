-- 3. FACTS
-- FACT_SALES_DAILY (Grain: Date + Store + Family)
CREATE TABLE fact_sales_daily (
    date TEXT,
    store_nbr INTEGER,
    family TEXT,
    set_type TEXT,
    -- 'train' or 'test'
    sales REAL,
    onpromotion INTEGER,
    transactions REAL,
    transactions_missing INTEGER,
    dcoilwtico_filled REAL,
    -- Denormalized flags from bridge
    is_holiday INTEGER,
    is_event INTEGER,
    is_workday INTEGER,
    PRIMARY KEY (date, store_nbr, family),
    FOREIGN KEY (store_nbr) REFERENCES dim_store(store_nbr),
    FOREIGN KEY (family) REFERENCES dim_family(family),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);
-- FACT_SALES_WEEKLY (The Source of Truth)
CREATE TABLE fact_sales_weekly (
    week_start TEXT,
    year_week INTEGER,
    store_nbr INTEGER,
    family TEXT,
    -- Metrics
    sales_sum REAL,
    onpromotion_sum REAL,
    transactions_sum REAL,
    dcoilwtico_mean REAL,
    -- Holiday/Event Aggregates
    is_holiday_week INTEGER,
    is_event_week INTEGER,
    is_workday_week INTEGER,
    n_holidays_sum INTEGER,
    n_events_sum INTEGER,
    -- Feature Engineering Flags
    is_payday_proxy_max INTEGER,
    is_train_day_count INTEGER,
    is_test_day_count INTEGER,
    is_clean_history INTEGER,
    is_future INTEGER,
    -- 1 if week touches future (sales_sum is unknown/null)
    -- 0/1
    PRIMARY KEY (year_week, store_nbr, family),
    FOREIGN KEY (year_week) REFERENCES dim_week(year_week),
    FOREIGN KEY (store_nbr) REFERENCES dim_store(store_nbr),
    FOREIGN KEY (family) REFERENCES dim_family(family)
);