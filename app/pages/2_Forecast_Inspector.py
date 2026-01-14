import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
import os

# Fix Path to allow importing 'utils' from parent 'app' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.data_loader import load_weekly_data, get_hierarchy
from utils.modeling import run_hybrid_forecast
from components.ui import load_css, metric_card, deep_dive_alert

st.set_page_config(layout="wide", page_title="Forecast Inspector", initial_sidebar_state="expanded")
load_css("style.css")

def main():
    st.title("Forecast Inspector")
    st.markdown("### Operational Deep Dive (Store x SKU)")

    # Load Data
    df = load_weekly_data()
    if df.empty:
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Mode Selection
        mode = st.radio(
            "Operation Mode",
            ["Forecast (Future)", "Backtest (Verification)"],
            index=0
        )
        
        st.markdown("---")
        stores, families = get_hierarchy(df)
        
        # Filters
        selected_store = st.selectbox("Store Selection", stores, index=0)
        selected_family = st.selectbox("Product Category", families, index=families.index("GROCERY I") if "GROCERY I" in families else 0)
        
        st.markdown("---")
        horizon = st.slider("Forecast Horizon (Weeks)", 4, 16, 8)
        
        # Cutoff
        cutoff_date = None
        if mode == "Backtest (Verification)":
            min_date = df['week_start'].min()
            max_date = df['week_start'].max()
            default_cutoff = max_date - pd.Timedelta(weeks=8)
            cutoff_date = st.date_input("Training Cutoff", value=default_cutoff, min_value=min_date, max_value=max_date)
            cutoff_date = pd.to_datetime(cutoff_date)
        
        st.caption("Engine: PiecewiseHybrid | Build v2.2")

    # Run Logic
    model_mode = 'backtest' if "Backtest" in mode else 'forecast'
    train_end = cutoff_date if model_mode == 'backtest' else df['week_start'].max()
    
    with st.spinner("Calculating forecast..."):
        result = run_hybrid_forecast(df, selected_store, selected_family, train_end, horizon, mode=model_mode)

    if result is None:
        st.error("No data available for this selection.")
        st.stop()
        
    forecast_df = result['forecast']
    train_data = result['train_data']

    # --- Metrics Section ---
    render_metrics_section(result, model_mode)

    # --- Main Chart ---
    render_main_chart(train_data, forecast_df, model_mode, selected_store, selected_family)

    # --- Deep Dive ---
    render_deep_dive(result, forecast_df, model_mode)


def render_metrics_section(result, mode):
    wape_display = "N/A"
    bias_display = "N/A"
    wape_color = ""
    bias_color = "text-blue"
    
    if mode == 'backtest':
        valid = result['forecast'].dropna()
        if not valid.empty:
            y_true = valid['sales']
            y_pred = valid['yhat']
            if y_true.sum() > 0:
                wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))
                bias = np.sum(y_pred - y_true) / np.sum(np.abs(y_true))
                wape_display = f"{wape:.1%}"
                wape_color = "text-green" if wape < 0.20 else "text-red"
                bias_display = f"{'+' if bias > 0 else ''}{bias:.1%}"
                bias_color = "text-green" if abs(bias) < 0.1 else "text-red"
    
    total_vol = result['forecast']['yhat'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Demand Type", result['demand_type'], f"ADI: {result['adi']:.2f}", "text-blue")
    with col2:
        metric_card("Forecast Accuracy (WAPE)", wape_display, "Weighted Error", wape_color)
    with col3:
        metric_card("Systematic Bias", bias_display, "Over/Under Prediction", bias_color)
    with col4:
        metric_card("Projected Volume", f"{total_vol:,.0f}", f"Next {len(result['forecast'])} Weeks")
    
    st.markdown("<br>", unsafe_allow_html=True)


def render_main_chart(train_data, forecast_df, mode, store, family):
    st.markdown("<h3>Demand Trajectory</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='plot-container'>", unsafe_allow_html=True)
    
    fig = go.Figure()

    # Historical
    history_plot = train_data.tail(104)
    fig.add_trace(go.Scatter(
        x=history_plot['week_start'], y=history_plot['sales'],
        mode='lines', name='Historical Sales',
        line=dict(color='#1e293b', width=1.5), opacity=0.6
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_df['date'], y=forecast_df['yhat'],
        mode='lines+markers', name='Hybrid Forecast',
        line=dict(color='#2563eb', width=3),
        marker=dict(size=6, color='#2563eb')
    ))
    
    # Ground Truth
    if mode == 'backtest':
        fig.add_trace(go.Scatter(
            x=forecast_df['date'], y=forecast_df['sales'],
            mode='lines+markers', name='Actual Sales',
            line=dict(color='#10b981', width=2, dash='dot'),
            marker=dict(size=6, symbol='x', color='#10b981')
        ))

    fig.update_layout(
        title=dict(text=f"Sales vs Forecast: Store {store} - {family}", font=dict(size=14, color='#374151')),
        xaxis_title="Timeline", yaxis_title="Quantity Sold",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white", height=500, hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_deep_dive(result, forecast_df, mode):
    st.markdown("<h3>Strategic Analysis & Export</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
        st.markdown("**Underlying Model Strategy**")
        deep_dive_alert(result['demand_type'], result['adi'], result['cv2'])
        
        st.markdown("**Forecast Data**")
        display_cols = ['date', 'yhat']
        if mode == 'backtest':
            display_cols.insert(1, 'sales')
            forecast_df['error'] = forecast_df['yhat'] - forecast_df['sales']
            display_cols.append('error')
            
        st.dataframe(forecast_df[display_cols].set_index('date').style.format("{:.1f}"), use_container_width=True, height=200)
        
        # Export Button (Step 3 Requirement)
        csv = forecast_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f"forecast_store{result['forecast']['store_nbr'].iloc[0]}_{result['mode']}.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        if mode == 'backtest':
            st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
            forecast_df['cumulative_error'] = (forecast_df['yhat'] - forecast_df['sales']).cumsum()
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=forecast_df['date'], y=forecast_df['cumulative_error'],
                fill='tozeroy', mode='lines', line=dict(color='#6366f1'), name='Cumul. Error'
            ))
            fig_cum.update_layout(title="Cumulative Error Tracking", height=350)
            st.plotly_chart(fig_cum, use_container_width=True)
            
            # Top Errors Insight
            if 'error' in forecast_df.columns:
                worst_week = forecast_df.loc[forecast_df['error'].abs().idxmax()]
                st.caption(f"Largest Deviation: {worst_week['date'].date()} (Error: {worst_week['error']:.1f})")
                
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='plot-container'>", unsafe_allow_html=True)
            st.info("Ground truth data not available for error calculation in Forecast mode.")
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
