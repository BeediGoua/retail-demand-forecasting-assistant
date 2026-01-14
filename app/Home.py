import streamlit as st
from pathlib import Path
import sys
import os

# Adjust path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from components.ui import load_css
from utils.data_loader import load_weekly_data

# --- Page Config ---
st.set_page_config(
    page_title="Retail Forecasting Assistant",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Load CSS ---
load_css("style.css")

# --- HEADER & KPI ---
st.title("Retail Demand Assistant")
st.markdown("### Next-Gen Supply Chain Optimization Engine")

# Load Data for Global KPIs
df = load_weekly_data()
if not df.empty:
    total_active_series = df[['store_nbr', 'family']].drop_duplicates().shape[0]
    total_sales_volume = df['sales'].sum()
    last_date = df['week_start'].max()
    
    # Calculate simple growth (Last 4 weeks vs Prev 4 weeks)
    weekly_agg = df.groupby('week_start', observed=True)['sales'].sum()
    last_4_avg = weekly_agg.tail(4).mean()
    prev_4_avg = weekly_agg.iloc[-8:-4].mean()
    growth = (last_4_avg - prev_4_avg) / prev_4_avg if prev_4_avg > 0 else 0

    st.markdown("---")
    st.header(f"System Pulse (As of {last_date.date()})")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        # Baseline Accuracy Proxy (Global WAPE from audit)
        st.metric("Model Baseline WAPE", "9.3%", "-0.8% vs Legacy", help="Global error rate of PiecewiseHybrid model")
        st.caption("Validated Benchmark")

    with kpi2:
        # Latest Demand Trend
        st.metric("Demand Momentum (4W)", f"{growth:+.1%}", "vs Prev Month", 
                 delta_color="normal" if growth > 0 else "inverse")
        st.caption("Short-term Sales Velocity")

    with kpi3:
        st.metric("Active Series (Scope)", f"{total_active_series:,.0f}", "Store x SKU Pairs")
        st.caption("Full Portfolio Coverage")

    with kpi4:
        st.metric("Last Data Point", last_date.strftime('%Y-%m-%d'), "Weekly Update")
        st.caption("Data Freshness")

else:
    st.warning("Data not loaded. Check connection.")


# --- EXECUTIVE SUMMARY ---
st.markdown("""
<div class="hero-box">
    <strong>Executive Summary</strong>: 
    This system transforms raw sales history into <strong>Actionable Inventory Decisions</strong>. 
    By combining statistical baselines with advanced Gradient Boosting (LightGBM/CatBoost), 
    we predict demand weeks in advance to minimize <strong>Lost Sales</strong> and <strong>Overstock Waste</strong>.
</div>
""", unsafe_allow_html=True)


# --- CONTEXT ---
st.markdown("---")
st.header("Project Context & Capabilities")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="hero-box" style="background-color: #F3E5F5; border-left: 5px solid #7B1FA2;">
        <h4>1. The Challenge: Retail Uncertainty</h4>
        <ul>
            <li><strong>Erratic Demand</strong>: Promotions, holidays, and local events create noise.</li>
            <li><strong>Sparse Data</strong>: Many items have intermittent sales (zeros), fooling traditional models.</li>
            <li><strong>Scale</strong>: Managing thousands of SKU/Store combinations manually is impossible.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="hero-box" style="background-color: #E0F2F1; border-left: 5px solid #00695C;">
        <h4>2. The Solution: AI-Driven Assistant</h4>
        <ul>
            <li><strong>Hybrid Engine</strong>: Automatically switches between Intermittent (Croston) and Dense (GBM) models.</li>
            <li><strong>Strategic Planning</strong>: Aggregated views for Category Managers.</li>
            <li><strong>Operational Precision</strong>: Granular SKU-level forecasts for Store Managers.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- NAVIGATION ---
st.markdown("---")
st.header("Tools & Modules")

nav1, nav2, nav3 = st.columns(3)

with nav1:
    st.markdown("""
    <div class="nav-card">
        <h4>Business Insights</h4>
        <p>Strategic view. Analyze aggregated trends, seasonality, and overall category performance.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Insights", use_container_width=True):
        st.switch_page("pages/1_Business_Insights.py")

with nav2:
    st.markdown("""
    <div class="nav-card">
        <h4>Forecast Inspector</h4>
        <p>Operational deep-dive. Inspect specific Store-Item forecasts and verify backtest accuracy.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Inspector", use_container_width=True):
        st.switch_page("pages/2_Forecast_Inspector.py")

with nav3:
    st.markdown("""
    <div class="nav-card">
        <h4>Methodology</h4>
        <p>Technical documentation. Understand the Hybrid Model logic, metrics, and data pipeline.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Read Docs", use_container_width=True, disabled=True):
        st.write("(Coming Soon)")

st.markdown("---")
st.caption("Retail Demand Assistant | Built with Streamlit & Plotly")
