from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Generator

def get_weekly_rolling_cv(
    df: pd.DataFrame, 
    min_train_weeks: int = 52, 
    horizon: int = 8, 
    step: int = 4
) -> Generator[tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """
    Generator for Rolling-Origin Cross-Validation splits on clean weekly history.
    
    Args:
        df: DataFrame containing 'week_start' and 'is_clean_history'.
        min_train_weeks: Minimum number of weeks for the first training set.
        horizon: Forecast horizon (e.g. 8 weeks).
        step: Step size between splits (e.g. 4 weeks).
        
    Yields:
        (train_split, valid_split)
    """
    
    # 1. Select only clean history weeks (exclude partial 2017-08-15)
    # We aggregate by week_start to get unique timeline
    timeline = df[df["is_clean_history"] == 1]["week_start"].drop_duplicates().sort_values().reset_index(drop=True)
    
    n_weeks = len(timeline)
    
    # Start iterating
    # We need at least min_train_weeks + horizon
    if n_weeks < min_train_weeks + horizon:
        raise ValueError(f"Not enough clean history ({n_weeks} weeks) for request (min={min_train_weeks}, h={horizon})")
    
    current_cutoff_idx = min_train_weeks
    
    fold = 1
    while current_cutoff_idx + horizon <= n_weeks:
        # Define ranges
        # Train: [0, current_cutoff_idx)
        # Valid: [current_cutoff_idx, current_cutoff_idx + horizon)
        
        train_weeks = timeline.iloc[:current_cutoff_idx]
        valid_weeks = timeline.iloc[current_cutoff_idx : current_cutoff_idx + horizon]
        
        cutoff_date = train_weeks.max()
        valid_date_start = valid_weeks.min()
        valid_date_end = valid_weeks.max()
        
        # Filter original DF
        train_split = df[df["week_start"].isin(train_weeks)].copy()
        valid_split = df[df["week_start"].isin(valid_weeks)].copy()
        
        print(f"Fold {fold}: Train end={cutoff_date.date()} | Valid=[{valid_date_start.date()} - {valid_date_end.date()}]")
        yield train_split, valid_split
        
        current_cutoff_idx += step
        fold += 1
