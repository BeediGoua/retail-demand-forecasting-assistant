import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
import os

# Fix Path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.data_loader import load_weekly_data
from components.ui import load_css

st.set_page_config(layout="wide", page_title="Business Insights", initial_sidebar_state="expanded")
load_css("style.css")

# --- DATA LOADING ---
df_raw = load_weekly_data()
if df_raw.empty:
    st.error("No data available.")
    st.stop()

# --- HEADER & FILTERS ---
st.title("Strategic Business Insights")
st.markdown("### Market Intelligence & Performance Analytics")

with st.expander("Filter Data", expanded=True):
    f1, f2 = st.columns(2)
    with f1:
        families = sorted(df_raw['family'].unique())
        sel_families = st.multiselect("Filter by Category", families, default=[])
    with f2:
        stores = sorted(df_raw['store_nbr'].unique())
        sel_stores = st.multiselect("Filter by Store", stores, default=[])

# Filtering
df = df_raw.copy()
if sel_families:
    df = df[df['family'].isin(sel_families)]
if sel_stores:
    df = df[df['store_nbr'].isin(sel_stores)]

if df.empty:
    st.warning("No data matches filters.")
    st.stop()

# --- KPIS ---
col1, col2, col3, col4 = st.columns(4)

total_sales = df['sales'].sum()
avg_weekly = df.groupby('week_start', observed=True)['sales'].sum().mean()
best_week_date = df.groupby('week_start', observed=True)['sales'].sum().idxmax()
best_week_val = df.groupby('week_start', observed=True)['sales'].sum().max()

# Year over Year logic (approximate)
df['year'] = df['week_start'].dt.year
current_year = df['year'].max()
prev_year_sales = df[df['year'] == current_year - 1]['sales'].sum()
curr_year_sales_ytd = df[df['year'] == current_year]['sales'].sum()

col1.metric("Total Sales Volume", f"{total_sales:,.0f}")
col2.metric("Avg Weekly Demand", f"{avg_weekly:,.0f}")
col3.metric("Peak Sales Week", f"{best_week_date.strftime('%Y-%m-%d')}")
col4.metric("Active SKUs", f"{df[['store_nbr', 'family']].drop_duplicates().shape[0]}")

st.markdown("---")

# --- TABBED ANALYSIS ---
tab1, tab2, tab3 = st.tabs(["Global Trends", "Seasonality", "Category Mix"])


with tab1:
    st.markdown("#### Sales Evolution")
    
    # Aggregated Trend
    daily_agg = df.groupby('week_start', observed=True)['sales'].sum().reset_index()
    
    # Moving Average for smoothness
    daily_agg['Trend (4W)'] = daily_agg['sales'].rolling(4).mean()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=daily_agg['week_start'], y=daily_agg['sales'], mode='lines', name='Weekly Sales', line=dict(color='#94a3b8', width=1)))
    fig_trend.add_trace(go.Scatter(x=daily_agg['week_start'], y=daily_agg['Trend (4W)'], mode='lines', name='Trend (4W Avg)', line=dict(color='#2563eb', width=3)))
    
    fig_trend.update_layout(height=400, template="plotly_white", hovermode="x unified", margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Insight
    last_4_avg = daily_agg.tail(4)['sales'].mean()
    prev_4_avg = daily_agg.iloc[-8:-4]['sales'].mean()
    growth = (last_4_avg - prev_4_avg) / prev_4_avg if prev_4_avg > 0 else 0
    
    st.markdown(f"""
    <div class="insight-box">
        <span class="insight-title">Momentum Indicator</span>
        Short-term momentum is <b style="color: {'#16a34a' if growth > 0 else '#dc2626'}">{growth:+.1%}</b> over the last month. 
        {'Demand is accelerating.' if growth > 0 else 'Demand is cooling down.'}
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("#### Annual Seasonal Profile")
    st.caption("How does demand behave throughout a typical year?")
    
    # Seasonality Analysis: Group by Week of Year
    df['week_of_year'] = df['week_start'].dt.isocalendar().week
    seasonal_profile = df.groupby('week_of_year')['sales'].mean().reset_index()
    
    fig_season = px.bar(seasonal_profile, x='week_of_year', y='sales', title="Average Sales by Week Number (1-52)",
                        color='sales', color_continuous_scale='Blues')
    fig_season.update_layout(height=450, template="plotly_white")
    st.plotly_chart(fig_season, use_container_width=True)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        peak_week = seasonal_profile.loc[seasonal_profile['sales'].idxmax(), 'week_of_year']
        st.markdown(f"""
        <div class="insight-box">
            <span class="insight-title">Peak Seasonality</span>
            The strongest selling period is typically <b>Week {peak_week}</b>. 
            Ensure stock levels are ramped up 2-3 weeks prior.
        </div>
        """, unsafe_allow_html=True)
    with col_s2:
        low_week = seasonal_profile.loc[seasonal_profile['sales'].idxmin(), 'week_of_year']
        st.markdown(f"""
        <div class="insight-box">
            <span class="insight-title">Low Seasonality</span>
            Demand is lowest around <b>Week {low_week}</b>. 
            Good time for maintenance or inventory audits.
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("#### Category Dynamics")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        cat_perf = df.groupby('family', observed=True)['sales'].sum().reset_index().sort_values('sales', ascending=True)
        # Top 15 categories to avoid clutter
        if len(cat_perf) > 15:
            cat_perf = cat_perf.tail(15)
            
        fig_bar = px.bar(cat_perf, y='family', x='sales', orientation='h', title="Top Categories by Volume", text_auto='.2s')
        fig_bar.update_layout(height=500, template="plotly_white")
        fig_bar.update_traces(marker_color='#0f766e', textfont_size=12)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        # Pareto Analysis
        cat_perf_desc = cat_perf.sort_values('sales', ascending=False)
        cat_perf_desc['cum_pct'] = cat_perf_desc['sales'].cumsum() / cat_perf_desc['sales'].sum()
        
        pareto_cutoff = cat_perf_desc[cat_perf_desc['cum_pct'] <= 0.8]['family'].count()
        total_cats = cat_perf_desc['family'].count()
        
        st.markdown(f"""
        <div class="hero-box">
            <h4 style="margin-top:0">Pareto Insight (80/20)</h4>
            <div style="font-size: 2rem; font-weight: 700; color: #0f766e;">{pareto_cutoff}</div>
            <div style="color: #64748b; font-size: 0.9rem;">Categories generate 80% of volume</div>
            <hr>
            <div style="font-size: 0.8rem; color: #94a3b8;">
                Total Categories: {total_cats}<br>
                Focus optimized forecasting on these top movers.
            </div>
        </div>
        """, unsafe_allow_html=True)


