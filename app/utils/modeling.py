import pandas as pd
import sys
import os

# Add project root to sys.path to allow importing from src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.baselines.optimized import PiecewiseHybrid
from src.baselines.models import SeasonalNaive, MovingAverage

def run_hybrid_forecast(df, store_nbr, family, train_end_date, horizon=8, mode='backtest'):
    """
    Runs the PiecewiseHybrid model for a specific store/family slice.
    
    Args:
        df (pd.DataFrame): The full dataframe
        store_nbr (int): Store ID
        family (str): Product Family
        train_end_date (pd.Timestamp): The cutoff date for training (ignored in forecast mode)
        horizon (int): Number of weeks to predict
        mode (str): 'backtest' or 'forecast'
        
    Returns:
        dict: containing 'forecast' (DataFrame), 'metrics' (dict), 'diagnostics' (dict)
    """
    # 1. Filter Data
    mask = (df['store_nbr'] == store_nbr) & (df['family'] == family)
    series_df = df[mask].copy().sort_values('week_start')
    
    if series_df.empty:
        return None

    # 2. Prepare Train Data
    if mode == 'forecast':
        # Use ALL available data for training
        train_data = series_df.copy()
        # Future dates start after the last data point
        last_date = series_df['week_start'].max()
    else:
        # Backtest mode: Cut off at train_end_date
        train_data = series_df[series_df['week_start'] <= train_end_date].copy()
        last_date = train_end_date

    # 3. Fit & Predict Hybrid
    model = PiecewiseHybrid()
    model.fit(train_data)
    
    # Predict into the future (relative to the training set)
    # The models are designed to predict 'horizon' weeks from the end of training data
    forecast_df = model.predict(horizon)
    
    # Robustness: Handle legacy or cached model output naming
    if 'sales_pred' in forecast_df.columns:
        forecast_df = forecast_df.rename(columns={'sales_pred': 'yhat'})
    
    if mode == 'backtest':
        # In backtest, we have ground truth
        test_data = series_df[
            (series_df['week_start'] > train_end_date) & 
            (series_df['week_start'] <= train_end_date + pd.Timedelta(weeks=horizon))
        ].copy()
        
        forecast_df = pd.merge(
            forecast_df, 
            test_data[['week_start', 'sales']], 
            left_on='date', 
            right_on='week_start', 
            how='left'
        )
        
        # Naive Baseline for Comparison
        naive = SeasonalNaive()
        naive.fit(train_data)
        naive_forecast = naive.predict(horizon)
        forecast_df['yhat_naive'] = naive_forecast['yhat']
        
    else:
        # In forecast mode, no ground truth, sales column is NaN or empty
        forecast_df['sales'] = None 
        forecast_df['yhat_naive'] = None # Optional: could compute naive forecast for future too

    return {
        'forecast': forecast_df,
        'demand_type': getattr(model, 'demand_type', 'Unknown'),
        'adi': getattr(model, 'adi', 0.0),
        'cv2': getattr(model, 'cv2', 0.0),
        'train_data': train_data,
        'mode': mode
    }
