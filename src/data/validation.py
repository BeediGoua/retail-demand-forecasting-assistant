from __future__ import annotations
import pandas as pd

def require_columns(df: pd.DataFrame, cols: list[str], name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: missing columns: {missing}")


def assert_unique_key(df: pd.DataFrame, key: list[str], name: str) -> None:
    dup = df.duplicated(key).sum()
    if dup != 0:
        raise ValueError(f"{name}: {dup} duplicated rows on key={key}")
