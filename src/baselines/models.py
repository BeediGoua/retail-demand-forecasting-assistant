import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class BaseForecastModel(ABC):
    @abstractmethod
    def fit(self, df):
        """Fit model on history."""
        pass

    @abstractmethod
    def predict(self, horizon, **kwargs):
        """Predict for next horizon steps."""
        pass

class SeasonalNaive(BaseForecastModel):
    """
    Predicts future values based on values from 'season_length' periods ago.
    Formula: Y(t) = Y(t - season_length)
    """
    def __init__(self, season_length=52, target_col='sales'):
        self.season_length = season_length
        self.target_col = target_col
        self.history = None

    def fit(self, df):
        """
        df must have 'year_week', 'store_nbr', 'family', and target_col.
        We just store the history needed for lookback.
        """
        self.history = df.copy()
        # Sort to ensure correct shift
        self.history = self.history.sort_values(by=['store_nbr', 'family', 'week_start'])
        return self

    def predict(self, horizon_weeks, future_dates=None):
        """
        Generates forecast for horizon_weeks.
        Returns DataFrame with keys + 'yhat'.
        """
        # In a real efficient implementation, we would do a join.
        # Here we take the last season_length weeks from history and project them forward.
        
        # This implementation assumes we are forecasting for *existing* series.
        # We shift the entire history by season_length weeks forward.
        
        forecasts = []
        
        # We iterate per group for clarity (can be vectorized for speed later)
        # But actually, vectorized shift is better.
        
        # Vectorized Approach:
        # Take the slice of history that corresponds to [End - season_length, End]
        # And map it to [End, End + season_length] (roughly)
        
        # Simplest Seasonal Naive Logic for "Next 8 weeks":
        # Find the values from (Now - 52 weeks) to (Now - 52 + 8 weeks)
        
        # Let's assume 'week_start' is datetime
        last_date = self.history['week_start'].max()
        # Dates we need to fetch from history:
        # [last_date - 52 weeks + 1 week, ... last_date - 52 weeks + 8 weeks]
        # Wait, Seasonal Naive usually means: Forecast(T+1) = Actual(T+1 - 52)
        
        # Let's implement looking up specific past dates.
        # This requires the history to be indexed by date preferably.
        
        h_indexed = self.history.set_index(['store_nbr', 'family', 'week_start'])[self.target_col]
        
        # Identify target dates
        # If future_dates is provided (list of dates), use valid dates.
        # Otherwise generate 8 weeks after last_date.
        
        # For simplicity in this baseline class:
        # We perform a "Shift 52 weeks" on the history and keep only rows that land in the future horizon.
        
        df_shifted = self.history.copy()
        df_shifted['pred_week_start'] = df_shifted['week_start'] + pd.to_timedelta(self.season_length, unit='W')
        
        # Filter only predictions that are in the future (after last history date)
        future_start = last_date + pd.to_timedelta(1, unit='D') # Roughly
        
        forecast = df_shifted[df_shifted['pred_week_start'] > last_date].copy()
        
        # Limit to horizon
        limit_date = last_date + pd.to_timedelta(horizon_weeks * 7 + 1, unit='D')
        forecast = forecast[forecast['pred_week_start'] <= limit_date]
        
        # Rename cols
        forecast = forecast.rename(columns={
            'pred_week_start': 'forecast_date',
            self.target_col: 'yhat'
        })
        
        return forecast[['forecast_date', 'store_nbr', 'family', 'yhat']]

class MovingAverage(BaseForecastModel):
    """
    Predicts future values based on average of last 'window' periods.
    Formula: Y(t) = Mean(Y(t-1)...Y(t-window))
    """
    def __init__(self, window=4, target_col='sales'):
        self.window = window
        self.target_col = target_col
        self.last_values = None

    def fit(self, df):
        # Compute the mean of the last 'window' weeks per series
        # We assume df is sorted
        # Group by store/family, take last window rows, mean
        
        grouped = df.sort_values('week_start').groupby(['store_nbr', 'family'], observed=True)
        
        # Calculate the mean of the last N observations
        self.last_values = grouped[self.target_col].apply(
            lambda x: x.tail(self.window).mean()
        ).reset_index()
        
        self.last_values.rename(columns={self.target_col: 'yhat_flat'}, inplace=True)
        self.last_date = df['week_start'].max()
        return self

    def predict(self, horizon_weeks):
        # Flat forecast: same value for all horizon steps
        # We need to replicate the row for each horizon step
        
        dates = [self.last_date + pd.to_timedelta((i+1)*7, unit='D') for i in range(horizon_weeks)]
        
        forecasts = []
        for d in dates:
            temp = self.last_values.copy()
            temp['forecast_date'] = d
            forecasts.append(temp)
            
        final_df = pd.concat(forecasts)
        final_df.rename(columns={'yhat_flat': 'yhat'}, inplace=True)
        
        return final_df[['forecast_date', 'store_nbr', 'family', 'yhat']]

class CrostonSBA(BaseForecastModel):
    """
    Croston method with Syntetos-Boylan Approximation (SBA).
    Good for intermittent demand.
    Formula: Y_hat = 0.95 * (Z / P)
    Where Z = Smoothed non-zero demand size
          P = Smoothed inter-demand interval
    """
    def __init__(self, alpha=0.1, target_col='sales'):
        self.alpha = alpha
        self.target_col = target_col
        self.forecasts = None
        self.last_date = None

    def fit(self, df):
        # Implementation of simple static Croston (not updating every step for horizon, just last state)
        # Group by series
        # We need to compute Z and P at the end of history
        
        def calculate_croston(series):
            # values: numpy array of demand
            values = series.values
            n = len(values)
            
            # Initialization
            # First non-zero
            first_nz_idx = np.argmax(values > 0)
            if values[first_nz_idx] == 0: # All zeros
                return 0.0
            
            z = values[first_nz_idx]
            p = 1 + first_nz_idx
            q = p # time since last demand
            
            # Smoothing parameters (same for size and interval)
            a = self.alpha
            
            # Iterate
            for i in range(first_nz_idx + 1, n):
                y = values[i]
                if y > 0:
                    z = a * y + (1 - a) * z
                    p = a * q + (1 - a) * p
                    q = 1
                else:
                    q += 1
            
            # SBA Correction factor (1 - alpha/2)
            forecast = (1 - a/2) * (z / p)
            return forecast

        self.last_date = df['week_start'].max()
        grouped = df.sort_values('week_start').groupby(['store_nbr', 'family'], observed=True)[self.target_col]
        
        # Apply croston to each group
        # Note: This apply is slow for 1800 series in pure python loop, but okay for baseline prototype
        # Optim: Vectorize or use numba later if needed. 
        self.forecasts = grouped.apply(calculate_croston).reset_index(name='yhat_flat')
        
        return self

    def predict(self, horizon_weeks):
        # Croston produces a constant forecast rate
        dates = [self.last_date + pd.to_timedelta((i+1)*7, unit='D') for i in range(horizon_weeks)]
        
        results = []
        for d in dates:
            temp = self.forecasts.copy()
            temp['forecast_date'] = d
            results.append(temp)
            
        final = pd.concat(results)
        final.rename(columns={'yhat_flat': 'yhat'}, inplace=True)
        return final[['forecast_date', 'store_nbr', 'family', 'yhat']]

