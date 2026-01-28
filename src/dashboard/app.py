import streamlit as st

st.set_page_config(
    page_title="Retail Demand Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Retail Demand Forecasting Assistant")

st.markdown("""
### Welcome to the Strategic Command Center

This dashboard is designed to audit the forecasted demand, understand market drivers, and optimize inventory decisions for the **Corporación Favorita** retail chain.

#### The 'Brain' of the System
We are transitioning from a baseline statistical approach to a **Gradient Boosting Challenger** model. This tool allows us to audit the data "Story" before trusting the "Black Box".

---
### Navigation
Use the sidebar to explore:
- **1. The Market Story**: Deep dive into Sales Drivers (Oil, Promos, Earthquake).
- **2. Model Performance**: (Coming Soon) Compare Baseline vs Challenger.
- **3. Inventory Simulator**: (Coming Soon) Optimize stock based on financial risks.

""")

st.sidebar.info("Select a page above to begin analysis.")
st.sidebar.markdown("---")
st.sidebar.caption("v0.1.0 - Challenger Phase")
