from __future__ import annotations
import pandas as pd
import numpy as np
from .validation import assert_unique_key

def build_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["day_of_week"] = df["date"].dt.dayofweek.astype("int8")  # 0=Mon
    df["is_weekend"] = (df["day_of_week"] >= 5).astype("int8")
    df["month"] = df["date"].dt.month.astype("int8")
    df["year"] = df["date"].dt.year.astype("int16")

    # Payday proxy: 15th or last day of month
    last_dom = (df["date"] + pd.offsets.MonthEnd(0)).dt.day
    df["is_payday_proxy"] = ((df["date"].dt.day == 15) | (df["date"].dt.day == last_dom)).astype("int8")
    return df


def process_oil(oil: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    idx = pd.date_range(start_date, end_date, freq="D")
    oil2 = oil.set_index("date").reindex(idx)
    oil2["dcoilwtico"] = oil2["dcoilwtico"].ffill().bfill()
    oil2 = oil2.reset_index().rename(columns={"index": "date"})
    assert_unique_key(oil2, ["date"], "oil_filled")
    return oil2


def process_holidays_store_aware(holidays: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    """
    Output: (date, store_nbr) with aggregated holiday/event features.
    Avoids row explosion on merge.
    """
    print("Processing holidays (store-aware, aggregated)...")

    hol = holidays.copy()

    # Important: transferred=True means "holiday moved away from this date" -> treat as normal day
    hol = hol[hol["transferred"] == False].copy()  # keep False (incl. rows type='Transfer' that indicate actual celebration date)

    stores_map = stores[["store_nbr", "city", "state"]].copy()

    # Build store-level expansion
    nat = hol[hol["locale"] == "National"].copy()
    reg = hol[hol["locale"] == "Regional"].copy()
    loc = hol[hol["locale"] == "Local"].copy()

    # Cross join national to all stores (safe size: ~350 * 54)
    if len(nat) > 0:
        nat_exp = nat.merge(stores_map, how="cross")
    else:
        nat_exp = pd.DataFrame(columns=list(hol.columns) + ["store_nbr", "city", "state"])

    # Regional: locale_name is a state
    if len(reg) > 0:
        reg_exp = reg.merge(stores_map, left_on="locale_name", right_on="state", how="inner")
    else:
        reg_exp = pd.DataFrame(columns=list(hol.columns) + ["store_nbr", "city", "state"])

    # Local: locale_name is a city
    if len(loc) > 0:
        loc_exp = loc.merge(stores_map, left_on="locale_name", right_on="city", how="inner")
    else:
        loc_exp = pd.DataFrame(columns=list(hol.columns) + ["store_nbr", "city", "state"])

    exp = pd.concat([nat_exp, reg_exp, loc_exp], ignore_index=True)

    if exp.empty:
        # No holidays (should not happen), return empty agg frame
        return pd.DataFrame(columns=["date", "store_nbr", "is_holiday", "is_event", "is_workday", "is_bridge", "n_holidays", "n_events"])

    # Type flags
    exp["is_holiday"] = (exp["type"] == "Holiday").astype("int8")
    exp["is_event"] = (exp["type"] == "Event").astype("int8")
    exp["is_workday"] = (exp["type"] == "Work Day").astype("int8")
    exp["is_bridge"] = (exp["type"] == "Bridge").astype("int8")
    exp["is_transfer_type"] = (exp["type"] == "Transfer").astype("int8")

    # Aggregate to (date, store)
    agg = (
        exp.groupby(["date", "store_nbr"], as_index=False)
        .agg(
            is_holiday=("is_holiday", "max"),
            is_event=("is_event", "max"),
            is_workday=("is_workday", "max"),
            is_bridge=("is_bridge", "max"),
            is_transfer_type=("is_transfer_type", "max"),
            n_holidays=("is_holiday", "sum"),
            n_events=("is_event", "sum"),
        )
    )

    assert_unique_key(agg, ["date", "store_nbr"], "holidays_agg")
    return agg


def build_daily_grid(base: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Ensure complete daily grid for each (store_nbr, family) so lags/rolling are safe.
    """
    stores = base["store_nbr"].unique()
    families = base["family"].unique()
    dates = pd.date_range(start_date, end_date, freq="D")

    grid = (
        pd.MultiIndex.from_product([dates, stores, families], names=["date", "store_nbr", "family"])
        .to_frame(index=False)
    )
    return grid


def make_weekly(df: pd.DataFrame, agg_rules: dict) -> pd.DataFrame:
    """
    Weekly bucket based on Monday-start weeks.
    """
    df = df.copy()
    # Strict Monday Start: Date - dayofweek
    df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.dayofweek, unit="D")
    group_cols = ["week_start", "store_nbr", "family"]
    weekly = df.groupby(group_cols, as_index=False).agg(agg_rules)
    return weekly
