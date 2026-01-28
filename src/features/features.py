import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class RetailFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Robust Feature Engineering for Ecuadorean Retail Demand.
    Implements research findings: Payday Effect, Store Clustering, and Lags.
    """
    def __init__(self, include_lags=True):
        self.include_lags = include_lags
        
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        X should be the 'daily_canon' dataframe sorted by store, family, date.
        """
        df = X.copy()
        
        # --- 1. Calendar & Payday Features (The 'Quincena') ---
        # Payday is usually 15th and End of Month
        df['day'] = df['date'].dt.day
        
        # Distance to 15th (e.g. on 14th dist is 1, on 16th dist is 1)
        # We want a countdown or specific flag. 
        # Research showed Peak on 15th and 30/31.
        df['is_payday_15'] = (df['day'] == 15).astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        
        # [PILLAR 1] Payday Distance (Explicit Request)
        # Calculate days until next payday (15th or End of Month)
        # Setup targets: 15th and End
        # Heuristic: Min distance to 15 or 30 (approx)
        df['days_to_payday'] = df['day'].apply(lambda x: 15 - x if x < 15 else (30 - x if x < 30 else 0))
        # Keep only positive distance or abs? Usually "days until".
        # If today is 16, target is 30 -> 14 days. If today is 14, target is 15 -> 1 day.
        
        # --- 2. Store Cluster Interactions (The 'Weekend Explosion') ---
        # Research found Clusters 14, 5, 11 explode on weekends
        # We assume 'cluster' and 'is_weekend' columns exist from daily_canon
        if 'cluster' in df.columns and 'is_weekend' in df.columns:
            # Interaction Feature: Cluster ID * Is_Weekend
            # For Tree models, it's better to keep them separate categorical or manual interaction
            # We'll create a specific flag for High-Weekend-Lift Clusters
            high_lift_clusters = [14, 5, 11]
            df['is_weekend_high_lift'] = (df['cluster'].isin(high_lift_clusters) & (df['is_weekend'] == 1)).astype(int)

        # --- 3. Lag Features (Autoregression) ---
        # Crucial for time series. We lag SALES.
        # NOTE: This requires Dataframe to be sorted and grouped properly.
        # We assume input is already prepared or we do simple shifts if single series (dangerous).
        # In a real pipeline, we use a custom LagTransformer specifically handles grouping.
        # Here we define the logic but rely on external loop or highly optimized groupby for speed.
        
        # For simplicity in this transformer, we act on row-level features.
        # Complex lag generation usually happens BEFORE this step in the pipeline 
        # to avoid slow groupby-apply inside transform().
        
        # --- 4. Oil Trend (Macro) ---
        # Moving average of Oil to capture Trend vs Noise
        # Assuming data is daily contiguous
            df['oil_ma_7'] = df['dcoilwtico'].rolling(window=7, min_periods=1).mean()

        # --- 5. The Earthquake (Structural Break) ---
        # [PILLAR 3] Structural Break variable
        # Earthquake happened April 16, 2016. Impact lasted ~X weeks.
        # We flag the "Crisis Period" to isolate this behavior.
        crisis_start = pd.Timestamp('2016-04-16')
        crisis_end = pd.Timestamp('2016-05-31') # Approx 1.5 months shock
        
        # Global shock flag (or specific to Manabi if state column exists)
        df['is_earthquake_period'] = ((df['date'] >= crisis_start) & (df['date'] <= crisis_end)).astype(int)
        
        if 'state' in df.columns:
             # Even stronger: Interaction for affected zones
             # Manabi was epicenter.
             df['is_earthquake_manabi'] = (df['is_earthquake_period'] & (df['state'] == 'Manabi')).astype(int)
            
        return df

def create_lags(df, target_col='sales', lags=[7, 14, 28, 365]):
    """
    Optimized Lag Generation.
    Assumes df is MultiIndex [store, family, date] or sorted.
    This creates huge memory pressure if not careful.
    
    We shift by 'group_id' (store_family).
    """
    # Create temporal features
    df = df.copy()
    
    # We essentially need fast GroupBy Shift.
    # Polars is better for this, but in Pandas:
    # Ensure sorted
    df = df.sort_values(by=['store_nbr', 'family', 'date'])
    
    group_cols = ['store_nbr', 'family']
    
    for lag in lags:
        # Grouped Shift
        df[f'sales_lag_{lag}'] = df.groupby(group_cols)[target_col].shift(lag)
        
    return df
