from __future__ import annotations
from pathlib import Path
import pandas as pd
from .validation import require_columns, assert_unique_key

def load_raw_data(raw_data_dir: Path):
    """
    Loads train, test, stores, oil, holidays, transactions from raw csvs.
    Returns tuple of DataFrames.
    """
    print("Loading raw CSV files...")

    train = pd.read_csv(
        raw_data_dir / "train.csv",
        parse_dates=["date"],
        dtype={"store_nbr": "int16", "onpromotion": "int16"},
        low_memory=False,
    )
    test = pd.read_csv(
        raw_data_dir / "test.csv",
        parse_dates=["date"],
        dtype={"store_nbr": "int16", "onpromotion": "int16"},
        low_memory=False,
    )
    stores = pd.read_csv(
        raw_data_dir / "stores.csv",
        dtype={"store_nbr": "int16", "cluster": "int16"},
        low_memory=False,
    )
    oil = pd.read_csv(raw_data_dir / "oil.csv", parse_dates=["date"], low_memory=False)
    holidays = pd.read_csv(
        raw_data_dir / "holidays_events.csv", parse_dates=["date"], low_memory=False
    )
    transactions = pd.read_csv(
        raw_data_dir / "transactions.csv", parse_dates=["date"], low_memory=False
    )

    # Minimal schema checks
    require_columns(train, ["date", "store_nbr", "family", "sales", "onpromotion"], "train")
    require_columns(test, ["date", "store_nbr", "family", "onpromotion"], "test")
    require_columns(stores, ["store_nbr", "city", "state", "type", "cluster"], "stores")
    require_columns(oil, ["date", "dcoilwtico"], "oil")
    require_columns(holidays, ["date", "type", "locale", "locale_name", "description", "transferred"], "holidays")
    require_columns(transactions, ["date", "store_nbr", "transactions"], "transactions")

    # Keys uniqueness
    assert_unique_key(train, ["date", "store_nbr", "family"], "train")
    assert_unique_key(test, ["date", "store_nbr", "family"], "test")
    assert_unique_key(transactions, ["date", "store_nbr"], "transactions")
    assert_unique_key(oil, ["date"], "oil")

    # Memory / consistency
    train["family"] = train["family"].astype("category")
    test["family"] = test["family"].astype("category")

    print(f"train: {train.shape}  | test: {test.shape}")
    print(f"stores: {stores.shape} | oil: {oil.shape} | holidays: {holidays.shape} | transactions: {transactions.shape}")
    
    return train, test, stores, oil, holidays, transactions
