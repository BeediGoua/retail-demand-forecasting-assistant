-- 2. BRIDGE (Holidays/Events)
-- BRIDGE_EVENT_STORE_DAY (Grain: Date + Store)
CREATE TABLE bridge_event_store_day (
    date TEXT,
    store_nbr INTEGER,
    is_holiday INTEGER,
    -- 0/1
    is_event INTEGER,
    -- 0/1
    is_workday INTEGER,
    -- 0/1
    is_bridge INTEGER,
    -- 0/1
    is_transfer_type INTEGER,
    -- 0/1
    n_holidays INTEGER,
    n_events INTEGER,
    PRIMARY KEY (date, store_nbr),
    FOREIGN KEY (store_nbr) REFERENCES dim_store(store_nbr)
);