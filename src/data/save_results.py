import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import uuid

# Define paths to DBs
EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "experiments"
DB_FORECASTS = EXPERIMENTS_DIR / "forecasts.sqlite"
DB_METRICS = EXPERIMENTS_DIR / "metrics.sqlite"
DB_DECISIONS = EXPERIMENTS_DIR / "decisions.sqlite"

def get_connection(db_path):
    """Creates a connection to a specific SQLite DB."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to {db_path}: {e}")
        return None

def register_run(train_end_year_week, model_family, params, horizon=8, grain="weekly"):
    """
    Registers a new experiment run in forecasts.sqlite (dim_runs).
    Returns the run_id.
    """
    run_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    params_json = json.dumps(params)
    
    conn = get_connection(DB_FORECASTS)
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dim_runs (run_id, created_at, grain, horizon, train_end_year_week, model_family, params_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run_id, created_at, grain, horizon, train_end_year_week, model_family, params_json))
            conn.commit()
            print(f"Run registered: {run_id}")
            return run_id
        except sqlite3.Error as e:
            print(f"Error registering run: {e}")
        finally:
            conn.close()
    return None

def save_forecasts(df_forecasts, run_id):
    """
    Saves forecasts to fact_forecasts_weekly in forecasts.sqlite.
    df_forecasts must have columns: year_week, store_nbr, family, horizon_step, yhat_mean, yhat_p10, yhat_p50, yhat_p90
    """
    df = df_forecasts.copy()
    df["run_id"] = run_id
    
    conn = get_connection(DB_FORECASTS)
    if conn:
        try:
            df.to_sql("fact_forecasts_weekly", conn, if_exists="append", index=False)
            print(f"Saved {len(df)} forecast rows for run {run_id}")
        except Exception as e:
            print(f"Error saving forecasts: {e}")
        finally:
            conn.close()

def save_metrics(df_metrics, run_id):
    """
    Saves metrics to fact_backtest_metrics in metrics.sqlite.
    df_metrics must have columns: metric_name, segment_type, segment_value, value, n_obs
    """
    df = df_metrics.copy()
    df["run_id"] = run_id
    
    conn = get_connection(DB_METRICS)
    if conn:
        try:
            df.to_sql("fact_backtest_metrics", conn, if_exists="append", index=False)
            print(f"Saved {len(df)} metric rows for run {run_id}")
        except Exception as e:
            print(f"Error saving metrics: {e}")
        finally:
            conn.close()

def save_decisions(df_decisions, run_id):
    """
    Saves decisions to fact_inventory_decisions_weekly in decisions.sqlite.
    df_decisions must have columns: year_week, store_nbr, family, order_qty, safety_stock, service_level, policy
    """
    df = df_decisions.copy()
    df["run_id"] = run_id
    
    conn = get_connection(DB_DECISIONS)
    if conn:
        try:
            df.to_sql("fact_inventory_decisions_weekly", conn, if_exists="append", index=False)
            print(f"Saved {len(df)} decision rows for run {run_id}")
        except Exception as e:
            print(f"Error saving decisions: {e}")
        finally:
            conn.close()
