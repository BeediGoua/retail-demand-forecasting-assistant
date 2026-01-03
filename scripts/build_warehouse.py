import sqlite3
import pandas as pd
from pathlib import Path

# Paths
DB_PATH = "data/retail.sqlite"

DATA_DIR = Path("data/processed")

def build_warehouse():
    print(f"BUILDING WAREHOUSE: {DB_PATH}")
    
    # 1. Init DB and Apply Schema
    # remove old if needed? let's keep it additive or drop tables in schema
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    print("Applying Schema...")

    # Get all .sql files in sql/ directory, sorted by name
    sql_files = sorted(Path("sql").glob("*.sql"))
    
    if not sql_files:
        print("WARNING: No SQL files found in sql/ directory!")
        
    for sql_file in sql_files:
        print(f"  -> Executing {sql_file.name}...")
        with open(sql_file, "r") as f:
            cur.executescript(f.read())
            
    con.commit()
    print("Schema applied successfully.")
    
    # helper
    def load_parquet_to_sql(parquet_path: Path, table_name: str, rename_map: dict = None, drop_cols: list = None):
        if not parquet_path.exists():
            print(f"Skipping {table_name}: File not found.")
            return

        print(f"Loading {table_name} from {parquet_path.name}...")
        df = pd.read_parquet(parquet_path)
        
        # Datetime conversion for SQLite (Text)
        for col in df.select_dtypes(include=['datetime64[ns]']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d')
            
        if rename_map:
            df = df.rename(columns=rename_map)
            
        if drop_cols:
            df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')
            
        # Append to table
        try:
            # We use 'append' because table exists from schema.
            # However, pandas might fail if schema mismatch. 
            # Best practice: strict insertion or using if_exists='append'
            df.to_sql(table_name, con, if_exists='append', index=False)
            print(f"Loaded {len(df):,} rows into {table_name}.")
        except Exception as e:
            print(f"ERROR loading {table_name}: {e}")

    # 2. Load Dimensions
    load_parquet_to_sql(DATA_DIR / "dim_store.parquet", "dim_store")
    load_parquet_to_sql(DATA_DIR / "dim_family.parquet", "dim_family")
    load_parquet_to_sql(DATA_DIR / "dim_calendar.parquet", "dim_date")

    # DIM_WEEK (Derived)
    print("Deriving dim_week...")
    cur.execute("""
        INSERT INTO dim_week (year_week, iso_year, iso_week, week_start_date, week_end_date)
        SELECT year_week, MAX(iso_year), MAX(iso_week), MIN(week_start_date), MAX(week_end_date) 
        FROM dim_date
        WHERE year_week IS NOT NULL
        GROUP BY year_week
    """)
    con.commit()

    # 3. Load Bridge
    load_parquet_to_sql(DATA_DIR / "bridge_event_store_day.parquet", "bridge_event_store_day")

    # 4. Load Facts
    # Mapping needed for daily
    # Schema: ... dcoilwtico_filled ... set_type ...
    # Parquet: ... dcoilwtico ... set ...
    # Mapping for daily
    daily_map = {
        "dcoilwtico": "dcoilwtico_filled",
        "set": "set_type"
    }
    # Drop columns not in schema (id + denormalized store columns + extra flags + denormalized calendar)
    extra_daily = [
        "id", 
        "city", "state", "type", "cluster", 
        "is_bridge", "is_transfer_type", "n_holidays", "n_events",
        "day_of_week", "year", "month", "day", "quarter", "is_weekend",
        "iso_year", "iso_week", "year_week", 
        "is_month_end", "is_payday_proxy", 
        "week_start", "week_end",
        "is_train_day", "is_test_day"
    ]
    # Check what else is in daily_canon: is_bridge, is_transfer_type, n_holidays, n_events are in process but not in daily schema
    load_parquet_to_sql(DATA_DIR / "daily_canon.parquet", "fact_sales_daily", rename_map=daily_map, drop_cols=extra_daily)
    
    # Mapping for weekly
    weekly_map = {
        "sales": "sales_sum",
        "onpromotion": "onpromotion_sum",
        "transactions": "transactions_sum",
        "dcoilwtico": "dcoilwtico_mean",
        "is_holiday": "is_holiday_week",
        "is_event": "is_event_week",
        "is_workday": "is_workday_week",
        "n_holidays": "n_holidays_sum",
        "n_events": "n_events_sum",
        "is_payday_proxy": "is_payday_proxy_max",
        "is_train_day": "is_train_day_count",
        "is_test_day": "is_test_day_count"
    }
    # Drop columns not in schema
    extra_weekly = ["transactions_missing", "is_bridge", "is_transfer_type"] 
    # Also check if other columns need dropping. The error complained about is_bridge.
    load_parquet_to_sql(DATA_DIR / "weekly_canon.parquet", "fact_sales_weekly", rename_map=weekly_map, drop_cols=extra_weekly)

    # Verification
    print("\n--- Verification ---")
    c_daily = cur.execute("SELECT COUNT(*) FROM fact_sales_daily").fetchone()[0]
    c_weekly = cur.execute("SELECT COUNT(*) FROM fact_sales_weekly").fetchone()[0]
    
    print(f"Row Count Daily:  {c_daily:,}")
    print(f"Row Count Weekly: {c_weekly:,}")
    
    con.close()
    print("\nWarehouse built successfully!")

if __name__ == "__main__":
    build_warehouse()

