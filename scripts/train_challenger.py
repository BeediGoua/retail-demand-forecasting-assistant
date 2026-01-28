import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
import sys
import os

# Add root to path for imports
sys.path.append('.')
from src.features.features import RetailFeatureEngineer, create_lags

def train_and_evaluate():
    print("--- 1. Loading Data ---")
    try:
        df = pd.read_parquet('data/processed/daily_canon.parquet')
        df = df.sort_values(by=['store_nbr', 'family', 'date']).reset_index(drop=True)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("--- 2. Feature Engineering ---")
    # Lags
    df_features = create_lags(df, lags=[7, 14, 28])
    
    # Custom Features
    engineer = RetailFeatureEngineer()
    df_features = engineer.transform(df_features)
    
    # Drop NaNs from Lags
    df_features = df_features.dropna(subset=['sales_lag_28'])
    
    # CRITICAL FIX: Tweedie fails on NaN target. Ensure 'sales' is clean.
    # Sales shouldn't be NaN in train set, but let's be safe.
    df_features = df_features.dropna(subset=['sales']) 
    
    print(f"Data ready: {df_features.shape}")

    print("--- 3. Splitting Data (Validation: Aug 2017) ---")
    split_date = '2017-08-01'
    mask_train = df_features['date'] < split_date
    mask_val = (df_features['date'] >= split_date) & (df_features['is_train_day'] == 1)

    X = df_features.drop(columns=['sales', 'date', 'id', 'set', 'transactions', 'transactions_missing'])
    y = df_features['sales']

    # Identify Categoricals
    # Note: In the notebook we listed these. CatBoost needs indices or names.
    cat_cols = ['store_nbr', 'family', 'city', 'state', 'type', 'cluster']
    # Ensure they exist
    cat_features = [c for c in cat_cols if c in X.columns]
    
    # Fill Nans in categorical if any (parquet shouldn't have them but for safety)
    for c in cat_features:
        X[c] = X[c].astype(str)

    X_train = X[mask_train]
    y_train = y[mask_train]
    X_val = X[mask_val]
    y_val = y[mask_val]

    print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")

    print("--- 4. Training CatBoost ---")
    model = CatBoostRegressor(
        iterations=500,
        learning_rate=0.1,
        depth=8,
        loss_function='Tweedie:variance_power=1.5',
        eval_metric='RMSE',
        random_seed=42,
        verbose=100,
        allow_writing_files=False # Keep it clean
    )

    train_pool = Pool(X_train, y_train, cat_features=cat_features)
    val_pool = Pool(X_val, y_val, cat_features=cat_features)

    model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=50)

    print("--- 5. Evaluation ---")
    preds = model.predict(X_val)
    preds = np.maximum(preds, 0)
    
    # WAPE
    wape = np.sum(np.abs(y_val - preds)) / np.sum(y_val)
    print(f"\n>>> FINAL VALIDATION WAPE: {wape:.4f}")
    
    # Feature Importance
    importances = model.get_feature_importance()
    feature_names = X_train.columns
    
    fi = pd.DataFrame({'feature': feature_names, 'importance': importances})
    fi = fi.sort_values(by='importance', ascending=False).head(15)
    
    print("\n>>> TOP 15 FEATURES:")
    print(fi)

if __name__ == "__main__":
    train_and_evaluate()
