import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_raw_data():
    """
    Loads raw datasets from the data/raw directory.
    Cached to improve dashboard performance.
    """
    # Robust path handling depending on where streamlit is run from
    # Assuming running from root or src/dashboard
    
    # Try finding data dir relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 3 levels: src/dashboard/utils -> src/dashboard -> src -> root
    root_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
    data_path = os.path.join(root_dir, "data/raw")
    
    if not os.path.exists(data_path):
        st.error(f"Data directory not found at: {data_path}")
        return None, None, None, None

    try:
        train = pd.read_csv(os.path.join(data_path, "train.csv"), parse_dates=['date'])
        oil = pd.read_csv(os.path.join(data_path, "oil.csv"), parse_dates=['date'])
        stores = pd.read_csv(os.path.join(data_path, "stores.csv"))
        transactions = pd.read_csv(os.path.join(data_path, "transactions.csv"), parse_dates=['date'])
        holidays = pd.read_csv(os.path.join(data_path, "holidays_events.csv"), parse_dates=['date'])
        
        return train, oil, stores, transactions, holidays
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return None, None, None, None, None

def get_merged_data():
    """
    Returns a merged sample of data for quick analysis
    """
    train, oil, stores, transactions, holidays = load_raw_data()
    
    if train is None:
        return None
        
    # Merge for context (Left join to keep all sales)
    df = train.merge(oil, on='date', how='left')
    df = df.merge(stores, on='store_nbr', how='left')
    
    # Fill missing oil with forward fill (standard practice)
    df['dcoilwtico'] = df['dcoilwtico'].ffill().bfill()
    
    return df
