import pandas as pd
from pathlib import Path

PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def create_calendar(start_date="2013-01-01", end_date="2017-08-31"):
    """
    Creates a standard Calendar Dimension table for SQL.
    Useful for joins, filtering by week/month/year, and navigating hierarchy.
    """
    print(f"Generating Calendar Dimension: {start_date} to {end_date}")
    
    dates = pd.date_range(start_date, end_date, freq="D")
    df = pd.DataFrame({"date": dates})
    
    # Basic
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
    df["year"] = df["date"].dt.year.astype("int32") # int32 to avoid overflow if multiplied
    df["month"] = df["date"].dt.month.astype("int8")
    df["day"] = df["date"].dt.day.astype("int8")
    df["quarter"] = df["date"].dt.quarter.astype("int8")
    df["day_of_week"] = df["date"].dt.dayofweek.astype("int8") # 0=Mon, 6=Sun
    df["is_weekend"] = (df["day_of_week"] >= 5).astype("int8")
    
    # ISO Week (The reference for our Weekly Assistant)
    iso = df["date"].dt.isocalendar()
    df["iso_year"] = iso.year.astype("int32") # int32 essential for year*100
    df["iso_week"] = iso.week.astype("int8")
    df["year_week"] = (df["iso_year"] * 100 + df["iso_week"]).astype("int32") # Ex: 201301
    
    # Fiscal / Business
    # Payday Proxy (15th and Last Day)
    df["is_month_end"] = df["date"].dt.is_month_end.astype("int8")
    df["is_payday_proxy"] = ((df["day"] == 15) | (df["is_month_end"] == 1)).astype("int8")
    
    # Week Start/End (Strict Monday Start)
    # 0=Mon, 6=Sun. We want Date - dayofweek days.
    df["week_start_date"] = df["date"] - pd.to_timedelta(df["date"].dt.dayofweek, unit="D")
    df["week_end_date"] = df["week_start_date"] + pd.Timedelta(days=6)
    
    return df

def generate_calendar_dataset():
    # Make sure we cover full range + a bit of future if needed
    cal = create_calendar("2013-01-01", "2017-12-31")
    
    output_path = PROCESSED_DATA_DIR / "dim_calendar.parquet"
    cal.to_parquet(output_path, index=False)
    
    print(f"Saved Calendar Dimension to {output_path} ({len(cal)} rows)")
    print(cal.head(3).T)


