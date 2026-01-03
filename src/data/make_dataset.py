from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure src modules are found
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.data.load import load_raw_data
from src.data.process import (
    process_oil,
    process_holidays_store_aware,
    build_daily_grid,
    build_calendar_features,
    make_weekly
)
from src.data.validation import assert_unique_key

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def generate_sales_dataset():
    # 1. Load Data
    train, test, stores, oil, holidays, transactions = load_raw_data(RAW_DATA_DIR)

    # 2. Determine global date range
    start_date = min(train["date"].min(), test["date"].min())
    end_date = max(train["date"].max(), test["date"].max())
    print(f"Global date range: {start_date} to {end_date}")

    # 3. Process inputs
    oil_filled = process_oil(oil, start_date, end_date)
    hol_store = process_holidays_store_aware(holidays, stores)
    
    tx = transactions.copy()
    assert_unique_key(tx, ["date", "store_nbr"], "transactions")

    # 4. Build unified base and grid
    print("Building daily grid...")
    train2 = train.copy()
    test2 = test.copy()
    train2["set"] = "train"
    test2["set"] = "test"
    test2["sales"] = np.nan  # Unknown future

    base = pd.concat([train2, test2], ignore_index=True)
    grid = build_daily_grid(base[["date", "store_nbr", "family"]], start_date, end_date)

    # 5. Merge everything
    print("Merging data...")
    df = grid.merge(base, on=["date", "store_nbr", "family"], how="left")

    # Fill basic columns
    df["onpromotion"] = df["onpromotion"].fillna(0).astype("int16")
    df["sales"] = np.where(df["set"].eq("train") & df["sales"].isna(), 0.0, df["sales"])

    # Stores, Oil, Transactions, Holidays
    df = df.merge(stores, on="store_nbr", how="left")
    df = df.merge(oil_filled, on="date", how="left")
    
    df = df.merge(tx, on=["date", "store_nbr"], how="left")
    df["transactions_missing"] = df["transactions"].isna().astype("int8")
    store_median_tx = df.groupby("store_nbr")["transactions"].transform("median")
    df["transactions"] = df["transactions"].fillna(store_median_tx)
    
    df = df.merge(hol_store, on=["date", "store_nbr"], how="left")
    
    # Fill NA after merge
    for c in ["is_holiday", "is_event", "is_workday", "is_bridge", "is_transfer_type", "n_holidays", "n_events"]:
        df[c] = df[c].fillna(0).astype("int8")

    # 6. Feature Engineering
    df = build_calendar_features(df)

    # 7. Aggregation Weekly
    print("Aggregating Weekly...")
    # Helper to count days in train vs test
    df["is_train_day"] = (df["set"] == "train").astype("int8")
    df["is_test_day"] = (df["set"] == "test").astype("int8")

    agg_rules = {
        "sales": "sum",
        "onpromotion": "sum",
        "dcoilwtico": "mean",
        "transactions": "sum",
        "transactions_missing": "max",
        "is_holiday": "max",
        "is_event": "max",
        "is_workday": "max",
        "is_bridge": "max",
        "n_holidays": "sum",
        "n_events": "sum",
        "is_payday_proxy": "max",
        "is_train_day": "sum", # Count of days belonging to history
        "is_test_day": "sum",  # Count of days belonging to future/kaggle test
    }
    weekly = make_weekly(df, agg_rules)
    
    # Validation flag: A week is "clean history" only if it has 7 train days
    # (Or at least 0 test days, to support potential gaps if any, though grid ensures 7 days)
    weekly["is_clean_history"] = (weekly["is_test_day"] == 0).astype("int8")
    
    # FUTURE LOGIC FIX:
    # If a week touches the future (test set), we must NOT say sales=0. We must say sales=Unknown (NaN).
    # Otherwise models will learn that demand drops to zero at the end of time.
    weekly["is_future"] = (weekly["is_test_day"] > 0).astype("int8")
    weekly.loc[weekly["is_future"] == 1, "sales"] = np.nan
    
    # We also advise filtering out the "Mixed Week" (partial train / partial test) for training.
    # The mixed week is identified by (is_train_day > 0) & (is_test_day > 0).
    # For now, we keep it in the parquet but flagged via is_clean_history=0.
    
    # Stats on incomplete weeks
    incomplete_weeks = weekly[weekly["is_test_day"] > 0]["week_start"].unique()
    print(f"Weeks touching Test set: {incomplete_weeks}")



    # 8. Save
    daily_path = PROCESSED_DATA_DIR / "daily_canon.parquet"
    weekly_path = PROCESSED_DATA_DIR / "weekly_canon.parquet"
    
    # NEW: Export Dimensions & Bridge for SQL Mart
    dim_store_path = PROCESSED_DATA_DIR / "dim_store.parquet"
    dim_family_path = PROCESSED_DATA_DIR / "dim_family.parquet"
    bridge_path = PROCESSED_DATA_DIR / "bridge_event_store_day.parquet"
    
    # dim_store
    stores.to_parquet(dim_store_path, index=False)
    
    # dim_family
    families = pd.DataFrame({"family": sorted(df["family"].dropna().unique())})
    families.to_parquet(dim_family_path, index=False)
    
    # bridge (hol_store contains the exploded events per store/date)
    # Ensure we only keep relevant columns
    bridge_cols = ["date", "store_nbr", "is_holiday", "is_event", "is_workday", 
                   "is_bridge", "is_transfer_type", "n_holidays", "n_events"]
    # hol_store might have fewer rows than full grid, but that's fine (sparse bridge)
    # Actually, let's filter hol_store to be safe
    existing_cols = [c for c in bridge_cols if c in hol_store.columns]
    hol_store[existing_cols].to_parquet(bridge_path, index=False)

    # Core Facts
    df.to_parquet(daily_path, index=False)
    weekly.to_parquet(weekly_path, index=False)
    
    print(f"Saved: {daily_path} ({df.shape})")
    print(f"Saved: {weekly_path} ({weekly.shape})")
    print(f"Saved: {dim_store_path}")
    print(f"Saved: {dim_family_path}")
    print(f"Saved: {bridge_path}")



