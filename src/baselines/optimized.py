import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

class PiecewiseHybrid(BaseEstimator, RegressorMixin):
    """
    Optimized Piecewise Hybrid Baseline ("The Winner").
    
    Logic verified by rolling origin backtest:
    - Intermittent / Lumpy (ADI/CV2) -> MA(4)
    - Erratic -> 0.5 * SN(52) + 0.5 * MA(4)
    - Smooth -> 0.3 * SN(52) + 0.7 * MA(4)
    """
    
    def __init__(self, ma_window=4, season_len=52):
        self.ma_window = ma_window
        self.season_len = season_len
        self.demand_types_ = {}
        
    def fit(self, X, y=None):
        """
        X should be a dataframe with ['store_nbr', 'family', 'week_start', 'sales']
        OR a pivot table (series in rows, time in cols).
        For simplicity in this robust version, we prefer fitting on the whole panel structure.
        """
        if isinstance(X, pd.DataFrame):
            if 'sales' in X.columns:
                 self.df_history = X.copy()
            else:
                raise ValueError("Input dataframe must have 'sales' column.")
        return self
        
    def predict(self, horizon=8):
        """
        Generates forecast for the next 'horizon' weeks for all series in df_history.
        Returns DataFrame with keys.
        """
        df = self.df_history.copy()
        
        df['week_start'] = pd.to_datetime(df['week_start'])
        df = df.sort_values('week_start')
        
        panel = df.pivot_table(
            index=["store_nbr", "family"],
            columns="week_start",
            values="sales",
            aggfunc="sum"
        ).sort_index(axis=1)
        
        history_vals = panel.to_numpy() # Shape (n_series, n_weeks)
        index_df = panel.index.to_frame(index=False)
        
        start_date = panel.columns[-1]
        future_dates = [start_date + pd.Timedelta(weeks=i+1) for i in range(horizon)]
        
        all_forecasts = []
        
        for i in range(history_vals.shape[0]):
            y = history_vals[i, :]
            
            dtype = self._classify(y)
            self.demand_types_[i] = dtype
            
            pred_ma = self._moving_avg(y, h=horizon, window=self.ma_window)
            pred_sn = self._seasonal_naive(y, h=horizon, season_len=self.season_len)
            
            if dtype in ["intermittent", "lumpy"]:
                final = pred_ma
            elif dtype == "erratic":
                final = 0.5 * pred_sn + 0.5 * pred_ma
            else: # smooth
                final = 0.3 * pred_sn + 0.7 * pred_ma
                
            store = index_df.iloc[i]['store_nbr']
            fam = index_df.iloc[i]['family']
            
            for step, val in enumerate(final):
                all_forecasts.append({
                    "date": future_dates[step],
                    "store_nbr": store,
                    "family": fam,
                    "sales_pred": max(0.0, val),
                    "demand_type": dtype
                })
                
        return pd.DataFrame(all_forecasts)

    def _classify(self, y):
        """ADI/CV2 Classification"""
        y = y[~np.isnan(y)]
        n = len(y)
        nz = np.sum(y > 0)
        
        if nz == 0: return "intermittent"
        
        adi = n / nz
        ynz = y[y > 0]
        mu = ynz.mean()
        # CV2 = Variance / Mean^2
        if mu == 0: return "intermittent"
        cv2 = ynz.var(ddof=0) / (mu ** 2)
        
        if adi < 1.32 and cv2 < 0.49: return "smooth"
        if adi < 1.32 and cv2 >= 0.49: return "erratic"
        if adi >= 1.32 and cv2 < 0.49: return "intermittent"
        return "lumpy"

    def _moving_avg(self, y, h, window):
        if len(y) == 0: return np.zeros(h)
        w = min(window, len(y))
        val = np.mean(y[-w:])
        return np.full(h, val)

    def _seasonal_naive(self, y, h, season_len):
        n = len(y)
        if n < season_len:
            return np.full(h, y[-1] if n > 0 else 0.0)
            

        start_idx = n - season_len
        end_idx = start_idx + h

        vals = y[start_idx : end_idx]

        return vals
