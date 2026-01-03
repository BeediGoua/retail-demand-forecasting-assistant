-- 1. DIMENSIONS
-- DIM_STORE
CREATE TABLE dim_store (
    store_nbr INTEGER PRIMARY KEY,
    city TEXT,
    state TEXT,
    type TEXT,
    cluster INTEGER
);
-- DIM_FAMILY
CREATE TABLE dim_family (family TEXT PRIMARY KEY);
-- DIM_DATE (Grain: Daily)
CREATE TABLE dim_date (
    date TEXT PRIMARY KEY,
    -- ISO String YYYY-MM-DD
    date_str TEXT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    day_of_week INTEGER,
    is_weekend INTEGER,
    -- 0/1
    iso_year INTEGER,
    iso_week INTEGER,
    year_week INTEGER,
    is_month_end INTEGER,
    -- 0/1
    is_payday_proxy INTEGER,
    -- 0/1
    week_start_date TEXT,
    week_end_date TEXT
);
-- DIM_WEEK
CREATE TABLE dim_week (
    year_week INTEGER PRIMARY KEY,
    iso_year INTEGER,
    iso_week INTEGER,
    week_start_date TEXT,
    week_end_date TEXT
);