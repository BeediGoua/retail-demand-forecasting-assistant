import streamlit as st
import os

def load_css(file_name):
    """Loads a CSS file and injects it into the Streamlit app."""
    # Assuming the CSS file is in the 'assets' directory relative to the app root
    # We need to find the absolute path.
    # Current file is in app/components/ui.py
    # CSS is in app/assets/style.css
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # app/
    css_path = os.path.join(project_root, 'assets', file_name)
    
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def metric_card(title, value, subtext, color_class=""):
    """
    Renders a stylized metric card using HTML/CSS.
    """
    html = f"""
    <div class="metric-container animate-fade-in">
        <div class="metric-title">{title}</div>
        <div class="metric-value {color_class}">{value}</div>
        <div class="metric-subtext">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def deep_dive_alert(strategy, adi, cv2):
    """
    Renders a conditional alert box explaining the model strategy.
    """
    strat_lower = strategy.lower()
    
    if strat_lower == "smooth":
        alert_type = "alert-info"
        desc = "Demand is consistent. Moving Average acts as a low-pass filter."
    elif strat_lower == "intermittent":
        alert_type = "alert-warning"
        desc = "Demand is sparse (many zeros). Croston/SBA prevents over-forecasting."
    elif strat_lower in ["lumpy", "erratic"]:
        alert_type = "alert-success" # Using success color for visibility, though it's a tricky case
        desc = "Demand varies. Seasonal Naive captures repetitive patterns."
    else:
        alert_type = "alert-info"
        desc = "Unknown pattern."

    html = f"""
    <div class="custom-alert {alert_type} animate-fade-in">
        <strong>Strategy: {strategy}</strong><br>
        Stats: ADI={adi:.2f}, CV²={cv2:.2f}<br>
        <em>{desc}</em>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
