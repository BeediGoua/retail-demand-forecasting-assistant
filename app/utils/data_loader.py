import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_weekly_data():
    """
    Loads the canonical weekly data from parquet.
    Cached by Streamlit to avoid reloading on every interaction.
    """
    # Adjust path assuming running from root directory
    data_path = 'data/processed/weekly_canon.parquet'
    
    if not os.path.exists(data_path):
        st.error(f"Data file not found at: {data_path}")
        return pd.DataFrame()
        
    df = pd.read_parquet(data_path)
    
    # Ensure proper types
    if 'week_start' in df.columns:
        df['week_start'] = pd.to_datetime(df['week_start'])
    
    return df

@st.cache_data
def get_hierarchy(df):
    """
    Returns unique stores and families for dropdowns.
    """
    stores = sorted(df['store_nbr'].unique())
    families = sorted(df['family'].unique())
    return stores, families
